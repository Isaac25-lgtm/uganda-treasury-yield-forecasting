"""Parser tests on SYNTHETIC text fixtures that mimic the layout of official BoU documents.

The numbers below are illustrative fixtures for parser behaviour, not observed data,
except where a comment cites the official document a layout quirk was taken from.
"""

import math
from datetime import date

from ugtbill.parse_itt import parse_date_words, parse_itt
from ugtbill.parse_results import (mmy_from_price, parse_results_text, price_from_mmy,
                                   repair_double_dot)

RESULTS_2024 = """
                           PRESS RELEASE
                 RESULTS OF TREASURY BILLS AUCTION
                          AUCTION NO:1500
             AUCTION DATE: WEDNESDAY 06-NOVEMBER-2024
            SETTLEMENT DATE: THURSDAY 07-NOVEMBER-2024
MATURITIES (DAYS):        91                      182              364
   MATURITY DATE:      6-Feb-25                8-May-25          6-Nov-25
    CUT OFF PRICE:      97.390                  93.825            87.177
   ANN. DISC RATE:      10.469                  12.384            12.858
 MONEY MKT YIELD:       10.749                  13.199            14..750
  EFFECTIVE YIELD:      11.191                  13.636            14.752
         OFFERED:    25,000,000,000          75,000,000,000   255,000,000,000
        TENDERED:    38,590,400,000          92,369,300,000   317,462,500,000
    ACCEPTED BIDS    4,460,400,000           38,989,300,000   134,012,500,000
BID TO COVER RATIO       5.605                   1.924             1.903
                             MANAGEMENT
                            November 07, 2024
"""

# 2022 header layout ("HELD ON: ... ISSUE DATE:") and an N/A tenor (layout of issue 1203, 2025).
RESULTS_2022_NA = """
               RESULTS OF TREASURY BILLS AUCTION
AUCTION NO: 1501   HELD ON: 05-Jan-2022   ISSUE DATE: 06-Jan-2022
            MATURITIES:                          91 Days                  182 Days                  364 Days
       MATURITY DATE:                       07-Apr-2022                07-Jul-2022              05-Jan-2023
       CUT OFF PRICE:                              N/A                     95.980                     90.603
     MONEY MKT YIELD:                              N/A                      8.400                     10.400
"""

ITT_2026 = """
                                                 INVITATION TO TENDER
                                                  ISSUE NO 1600
OFFERED AMOUNT:                                                    350,000,000,000/=
ISIN      UG11B0810264              91 DAYS                         15,000,000,000/=
ISIN      UG11C0701271             182 DAYS                         35,000,000,000/=
ISIN      UG11E0807272             364 DAYS                        300,000,000,000/=
AUCTION DATE:                                                  Wednesday July 8, 2026
MATURITY DATES:
                                   91 DAYS                                08-Oct-2026
(CSD) by 10.00am, Wednesday July 8, 2026.
                                                             Thursday July 02, 2026
                                                                MANAGEMENT
"""


def test_results_values_and_keys():
    r = parse_results_text(RESULTS_2024)
    assert r["status"] == "ok"
    assert r["auction_no"] == 1500
    assert r["auction_date"] == date(2024, 11, 6)
    assert r["settlement_date"] == date(2024, 11, 7)
    assert r["printed_release_date"] == date(2024, 11, 7)
    t91 = r["tenors"][91]
    assert t91["cutoff_price"] == 97.390 and t91["mmy"] == 10.749
    assert t91["maturity_date"] == date(2025, 2, 6)
    assert t91["offered"] == 25_000_000_000
    assert t91["parse_flag"] == "ok"


def test_double_dot_typo_is_preserved_not_silently_fixed():
    t364 = parse_results_text(RESULTS_2024)["tenors"][364]
    assert t364["mmy_raw"] == "14..750"
    assert math.isnan(t364["mmy"])
    assert t364["parse_flag"] == "unparseable"
    assert repair_double_dot(t364["mmy_raw"]) == 14.750  # only in the declared sensitivity


def test_2022_header_and_not_awarded_tenor():
    r = parse_results_text(RESULTS_2022_NA)
    assert r["auction_date"] == date(2022, 1, 5)
    assert r["settlement_date"] == date(2022, 1, 6)
    assert r["tenors"][91]["parse_flag"] == "not_awarded"
    assert math.isnan(r["tenors"][91]["mmy"])
    assert r["tenors"][182]["mmy"] == 8.400


def test_image_only_document_is_not_guessed():
    r = parse_results_text("PRESS RELEASE\nRESULTS OF TREASURY BILLS AUCTION\nAUCTION NO:1232\n"
                           "AUCTION DATE: WEDNESDAY 08-JUL-2026\n")
    assert r["status"] == "no_text_layer"
    assert r["tenors"] == {}


def test_price_yield_identity_matches_official_example():
    # Official DOCX for auction 1235 (30-Sep-2026): 91-day cut-off 97.639, money-market yield 9.699.
    assert abs(mmy_from_price(97.639, 91) - 9.699) < 0.001
    assert abs(price_from_mmy(mmy_from_price(94.912, 182), 182) - 94.912) < 1e-9


def test_auction_1176_style_actual_day_count_differs_from_nominal():
    # 1176 printed 9.102 for price 97.805: consistent with 90 actual days, not 91 nominal days.
    assert abs(mmy_from_price(97.805, 91) - 9.102) > 0.05
    assert abs(mmy_from_price(97.805, 90) - 9.102) < 0.001


def test_itt_prebid_fields():
    r = parse_itt(ITT_2026)
    assert r["issue_no"] == 1600
    assert r["auction_date"] == date(2026, 7, 8)
    assert r["notice_date"] == date(2026, 7, 2)
    assert (r["offer_91"], r["offer_182"], r["offer_364"]) == (15e9, 35e9, 300e9)
    assert r["offer_total"] == 350e9
    assert r["bid_deadline"] == "10:00am"


def test_date_word_variants_seen_in_official_notices():
    assert parse_date_words("Wednesday January,03 2024.") == date(2024, 1, 3)
    assert parse_date_words("Wednesday 21, October 2026.") == date(2026, 10, 21)
    assert parse_date_words("Thursday 24, July 2025") == date(2025, 7, 24)
    assert parse_date_words("no date here") is None
