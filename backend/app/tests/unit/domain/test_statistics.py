"""groupedSum golden fixtures from uhabits EntryListTest.kt (testGroupByNumerical/Boolean)."""

from datetime import date, timedelta

from app.domain.models.entry import SKIP, YES_MANUAL, Entry
from app.domain.models.entry import next_toggle_value, NO, UNKNOWN, YES_AUTO
from app.domain.services.statistics import TruncateField, grouped_sum, truncate_date

OFFSETS = [
    0, 5, 9, 15, 17, 21, 23, 27, 28, 35, 41, 45, 47, 53, 56, 62, 70, 73, 78,
    83, 86, 94, 101, 106, 113, 114, 120, 126, 130, 133, 141, 143, 148, 151, 157, 164,
    166, 171, 173, 176, 179, 183, 191, 259, 264, 268, 270, 275, 282, 284, 289, 295,
    302, 306, 310, 315, 323, 325, 328, 335, 343, 349, 351, 353, 357, 359, 360, 367,
    372, 376, 380, 385, 393, 400, 404, 412, 415, 418, 422, 425, 433, 437, 444, 449,
    455, 460, 462, 465, 470, 471, 479, 481, 485, 489, 494, 495, 500, 501, 503, 507,
]

VALUES = [
    230, 306, 148, 281, 134, 285, 104, 158, 325, 236, 303, 210, 118, 124,
    301, 201, 156, 376, 347, 367, 396, 134, 160, 381, 155, 354, 231, 134, 164, 354,
    236, 398, 199, 221, 208, 397, 253, 276, 214, 341, 299, 221, 353, 250, 341, 168,
    374, 205, 182, 217, 297, 321, 104, 237, 294, 110, 136, 229, 102, 271, 250, 294,
    158, 319, 379, 126, 282, 155, 288, 159, 215, 247, 207, 226, 244, 158, 371, 219,
    272, 228, 350, 153, 356, 279, 394, 202, 213, 214, 112, 248, 139, 245, 165, 256,
    370, 187, 208, 231, 341, 312,
]

REFERENCE = date(2014, 6, 1)


def test_grouped_sum_numerical():
    entries = [Entry(REFERENCE - timedelta(days=o), v) for o, v in zip(OFFSETS, VALUES)]

    by_month = grouped_sum(entries, TruncateField.MONTH, is_numerical=True)
    assert len(by_month) == 17
    assert by_month[0] == Entry(date(2014, 6, 1), 230)
    assert by_month[6] == Entry(date(2013, 12, 1), 1988)
    assert by_month[12] == Entry(date(2013, 5, 1), 1271)

    by_quarter = grouped_sum(entries, TruncateField.QUARTER, is_numerical=True)
    assert len(by_quarter) == 6
    assert by_quarter[0] == Entry(date(2014, 4, 1), 3263)
    assert by_quarter[3] == Entry(date(2013, 7, 1), 3838)
    assert by_quarter[5] == Entry(date(2013, 1, 1), 4975)

    by_year = grouped_sum(entries, TruncateField.YEAR, is_numerical=True)
    assert by_year == [Entry(date(2014, 1, 1), 8227), Entry(date(2013, 1, 1), 16172)]


def test_grouped_sum_boolean():
    entries = [Entry(REFERENCE - timedelta(days=o), YES_MANUAL) for o in OFFSETS]

    by_month = grouped_sum(entries, TruncateField.MONTH, is_numerical=False)
    assert len(by_month) == 17
    assert by_month[0] == Entry(date(2014, 6, 1), 1_000)
    assert by_month[6] == Entry(date(2013, 12, 1), 7_000)
    assert by_month[12] == Entry(date(2013, 5, 1), 6_000)

    by_year = grouped_sum(entries, TruncateField.YEAR, is_numerical=False)
    assert by_year == [Entry(date(2014, 1, 1), 34_000), Entry(date(2013, 1, 1), 66_000)]


def test_grouped_sum_skip_counts_zero():
    entries = [Entry(date(2014, 6, 1), SKIP), Entry(date(2014, 6, 2), 500)]
    assert grouped_sum(entries, TruncateField.MONTH, is_numerical=True) == [
        Entry(date(2014, 6, 1), 500)
    ]


def test_truncate_week_respects_first_weekday():
    d = date(2015, 1, 25)  # a Sunday
    assert truncate_date(d, TruncateField.WEEK, first_weekday=0) == date(2015, 1, 19)  # Monday
    assert truncate_date(d, TruncateField.WEEK, first_weekday=6) == date(2015, 1, 25)  # Sunday


def test_next_toggle_value_cycle():
    # Port of Entry.nextToggleValue semantics.
    assert next_toggle_value(YES_AUTO, False, False) == YES_MANUAL
    assert next_toggle_value(YES_MANUAL, True, False) == SKIP
    assert next_toggle_value(YES_MANUAL, False, False) == NO
    assert next_toggle_value(SKIP, True, True) == NO
    assert next_toggle_value(NO, False, True) == UNKNOWN
    assert next_toggle_value(NO, False, False) == YES_MANUAL
    assert next_toggle_value(UNKNOWN, False, False) == YES_MANUAL
