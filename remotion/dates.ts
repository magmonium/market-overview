/**
 * The long date, as the still prints it — `Monday, October 12, 2026` / `সোমবার, 12 অক্টোবর, 2026`.
 *
 * ⚠️ **Parsed as UTC, never local.** `new Date('2026-10-12')` is midnight *UTC*, but `getDay()` reads the
 * machine's own zone — so a re-render on a laptop west of Greenwich would move the weekday back a day, and
 * `test_frame_identity.py`'s hard equality on the still would fail somewhere the cause is invisible.
 * `Date.UTC` + `getUTCDay()` is the same calendar day on every machine.
 *
 * ⚠️ **The order lives in the label table, not here.** English is `{weekday}, {month} {day}, {year}`; Bengali is
 * `{weekday}, {day} {month}, {year}`. Same reason `breadth.counted_note` is a phrase rather than a word: word order
 * differs between the languages and cannot be fixed in shared layout code.
 *
 * ⚠️ **Digits stay Latin in both editions**, matching `metadata.formatted_date`: the product's labels are Bengali and
 * its figures are numerals, so `12` rather than `১২`. Writing the day in Bengali numerals would make the still the one
 * surface where a reader has to convert.
 *
 * Total, like `headline`: a date it cannot parse comes back as the raw string rather than as `NaN` on the frame.
 */
export const longDate = (iso: string, table: Record<string, string>): string => {
  const [year, month, day] = iso.split('-').map(Number);
  const template = table.long;
  if (
    !template ||
    !Number.isInteger(year) ||
    !(month >= 1 && month <= 12) ||
    !(day >= 1 && day <= 31)
  ) {
    return iso;
  }
  const weekday = new Date(Date.UTC(year, month - 1, day)).getUTCDay();
  const slots: Record<string, string> = {
    '{weekday}': table[`weekday_${weekday}`] ?? '',
    '{month}': table[`month_${month}`] ?? '',
    '{day}': String(day),
    '{year}': String(year),
  };
  return Object.entries(slots).reduce(
    (text, [token, value]) => text.replaceAll(token, value),
    template
  );
};
