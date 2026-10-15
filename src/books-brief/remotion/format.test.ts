import assert from 'node:assert/strict';
import test from 'node:test';
import type {Book, Price} from './bundle.ts';
import {EN, tableFor} from './copy.ts';
import {countryLabel, digits, isoMondayLabel, languageLabel, money, moveLabel, number, percent, priceLine, publishedLabel, varies} from './format.ts';

/**
 * ⚠️ **The pure half of the render layer, tested the way the reel tests its own** — `node --test`, no bundler, no
 * browser. Everything here is a *value into a string*, which is exactly the half of ADR 0003 that can be checked without
 * rendering a frame.
 */

const book = (over: Partial<Book> = {}): Book => ({
  // ⚠️ The work key (ticket 32) — written the way `identity.work` would produce it, so a test that reads it is reading
  // the shape the conductor actually emits rather than a stand-in.
  key: 'ektishonarboi|sunilgangopadhyay',
  isbn: '9788172151234',
  rank: 7,
  weeks_on_chart: 3,
  is_new: false,
  move: 3,
  title: 'Ekti Shonar Boi',
  author: 'Sunil Gangopadhyay',
  publisher: 'Ananda Publishers',
  published: '2026-10',
  genre: 'fiction',
  country: 'in',
  language: 'bn',
  price: {amount: 399, currency: 'INR', retailer: 'amazon-in', edition: 'paperback', retailers: ['amazon-in']},
  identity: 'resolved',
  cover: null,
  ...over,
});

test('the Bengali chart counts in its own numerals', () => {
  // ⚠️ Ticket 27 — rank, price, Δ and the week number. The mapping is asserted **digit by digit**, because the whole
  // point of the table is which code point each numeral is: a shifted table still renders *something* that looks like
  // Bengali and is wrong, which is the failure a shape-level assertion cannot see.
  assert.equal(digits('0123456789', 'bn'), '০১২৩৪৫৬৭৮৯');
  assert.equal(digits('41', 'bn'), '৪১');
  assert.equal(digits('100', 'bn'), '১০০');
});

test('every other chart counts in Latin', () => {
  assert.equal(digits('41', 'en'), '41');
  assert.equal(digits(399, 'en'), '399');
});

test('a published date renders the precision that exists', () => {
  // ⚠️ Ticket 05 §2 — and the **unparseable** case is `null`, not a best effort: a guess is not replayable (ticket 03).
  assert.equal(publishedLabel('2026-10-14'), '14 Oct 2026');
  assert.equal(publishedLabel('2026-10'), 'Oct 2026');
  assert.equal(publishedLabel('2026'), '2026');
  assert.equal(publishedLabel(null), null);
  assert.equal(publishedLabel(''), null);
  assert.equal(publishedLabel('2026-13-45'), null, 'month 13 must not index past the table');
  assert.equal(publishedLabel('sometime in the autumn'), null);
});

test('NEW replaces the delta slot, and a missing comparison is not a zero', () => {
  // ⚠️ Ticket 07 — *"never a blank Δ, and never `▲0`"*. Both cases are `null`, and the slide prints NEW for one of them.
  assert.equal(moveLabel(book({is_new: true, move: null}), 'en'), null);
  assert.equal(moveLabel(book({move: null}), 'en'), null);
  assert.equal(moveLabel(book({move: 3}), 'en'), '▲ 3');
  assert.equal(moveLabel(book({move: -5}), 'en'), '▼ 5');
  // ⚠️ A genuine hold is neither an arrow nor a blank — it is a different fact from *no comparison*.
  assert.equal(moveLabel(book({move: 0}), 'en'), '\u2013');
});

test('the Bengali chart writes its delta in Bengali numerals too', () => {
  assert.equal(moveLabel(book({move: 3}), 'bn'), '▲ ৩');
});

test('"best" is only printed when there was a comparison to make', () => {
  // ⚠️ Ticket 04 — the *count* is Python's; this layer only reads it. One retailer is not a comparison, so the slide
  // names the shop and stops.
  const one: Price = {
    amount: 399, currency: 'INR', retailer: 'amazon-in', edition: 'paperback', retailers: ['amazon-in'],
  };
  const two: Price = {
    amount: 349, currency: 'INR', retailer: 'flipkart', edition: 'paperback', retailers: ['amazon-in', 'flipkart'],
  };

  assert.equal(priceLine(one, EN, 'en'), '₹399 · Amazon · paperback');
  assert.equal(priceLine(two, EN, 'en'), '₹349 · Flipkart · paperback');
  assert.equal(priceLine({...one, amount: null}, EN, 'en'), '\u2014 · Amazon · paperback', 'never ₹0');
});

test('money is currency-specific in its symbol, its grouping and its minor unit', () => {
  // ⚠️ ⚠️ **Three differences, and the comment this test replaced cited a superseded ticket for all three.**
  //
  // ⚠️ The old test said *"`en-IN`, because every chart is India-anchored (ticket 12)"* — and ticket 19 made the English
  // chart **US**, ticket 20 made the Bengali chart span **India and Bangladesh**, and ticket 22 made comics
  // **worldwide**. ⚠️ The premise had been false for three tickets and the assertion had been true the whole time,
  // because every price it was ever given was a rupee price.
  assert.equal(money(399, 'INR', 'en'), '₹399', 'the rupee, whole');
  assert.equal(money(129900, 'INR', 'en'), '₹1,29,900', 'lakh-grouped, because ₹1,29,900 is not ₹129,900');
  assert.equal(money(129900, 'USD', 'en'), '$129,900.00', 'and a dollar figure is NOT lakh-grouped');
  assert.equal(money(24.99, 'USD', 'en'), '$24.99', 'a dollar price has cents — the old code rounded to $25');
  assert.equal(money(180, 'BDT', 'en'), '৳180', 'Taka: the ৳ sign, whole, grouped the Western way');
  assert.equal(money(1234567, 'BDT', 'en'), '৳1,234,567', 'and not ₹12,34,567');
  // ⚠️ **And 2026-10-15 added the English chart's international stores**, which is what brought GBP, CAD and AUD into
  // the table. ⚠️ The two dollars are **not** USD — `amazon.ca` and `amazon.com.au` print a bare `$`, and the store is
  // the only thing that can tell them apart (`amazon.MARKETPLACES`), so a plain `$` here would be the wrong sign on a
  // real price.
  assert.equal(money(24.99, 'GBP', 'en'), '£24.99', 'the pound');
  assert.equal(money(24.99, 'CAD', 'en'), 'CA$24.99', 'Canadian dollars, never a bare $');
  assert.equal(money(24.99, 'AUD', 'en'), 'A$24.99', 'Australian dollars, never a bare $');
});

test('an unknown currency draws the number and no symbol', () => {
  // ⚠️ **A wrong symbol is worse than an absent one, because it is *assertive*.** A price whose denomination the
  // evidence does not state is one the slide may print as a bare number — it is never one it may label with the wrong
  // sign, and `prices.Price.currency` defaults to empty for exactly this reason.
  assert.equal(money(24.99, '', 'en'), '24.99');
  assert.equal(money(399, 'XYZ', 'en'), '399');
});

test('the still dates itself off the week key and never off a clock', () => {
  // ⚠️ ADR 0003 — `new Date()` here would make the still's date a property of *when it was rendered*.
  assert.equal(isoMondayLabel('2026-W41'), '5 OCT 2026');
  assert.equal(isoMondayLabel('2026-W01'), '29 DEC 2025', 'week 1 can begin in the previous year');
});

test('the market band writes a number and a signed percentage', () => {
  // ⚠️ Ticket 08 — the band reads as **background**, so its numerals are tabular and grouped the Indian way, and a
  // missing value is a dash rather than a zero (an index that did not resolve is not an index at zero).
  assert.equal(number(24812.35, 'en'), '24,812.35');
  assert.equal(number(null, 'en'), '\u2014');
  assert.equal(percent(0.42, 'en'), '+0.42%');
  assert.equal(percent(-0.12, 'en'), '\u22120.12%');
  assert.equal(percent(null, 'en'), '\u2014');
});

test('the band counts in the script its chart is set in', () => {
  // ⚠️ Ticket 27's four fields do not include the band, but the band sits **on the slide** — and a Bengali slide with
  // Latin numerals in its own market band would be the one place the script changed mid-frame.
  assert.equal(number(24812.35, 'bn'), '২৪,৮১২.৩৫');
  assert.equal(percent(0.42, 'bn'), '+০.৪২%');
});

test('the Bengali chart gets the Bengali label table', () => {
  assert.equal(tableFor('bn').new, 'নতুন');
  assert.equal(tableFor('en').new, 'NEW');
  // ⚠️ An unknown language falls back rather than refusing: a label table is copy, and a chart in the wrong *language*
  // is a smaller failure than a chart that will not render.
  assert.equal(tableFor('zz').new, 'NEW');
});

test('a label draws only where the chart disagrees with itself', () => {
  // ⚠️ **Ticket 20's whole rule, and the reason it is a function rather than a condition inside the slide.** A label that
  // says the same thing on all 100 rows is not information — the header already says BENGALI BOOKS — so the question that
  // matters is not *does India render* but *does a chart of identical rows render anything at all*.
  assert.equal(varies(['in', 'in', 'in']), false, 'a constant label is decoration');
  assert.equal(varies(['in', 'bd']), true, 'two countries on one chart is information');
  assert.equal(varies([]), false, 'no rows, no label');
});

test('the English chart now varies in country too', () => {
  // ⚠️ ⚠️ **Ticket 19 asserted the opposite for this chart and ticket 20's rule still holds** (2026-10-15): the chart
  // reads `us`, `gb`, `ca` and `au` lists, so the country label draws on it for the first time. ⚠️ The *language* still
  // does not vary — every one of those lists is `en` — so that label stays off.
  assert.equal(varies(['us', 'gb', 'ca', 'au']), true, 'four countries, so the label is information');
  assert.equal(varies(['en', 'en', 'en']), false, 'one language, so the label is decoration');
});

test('an empty label is not a variation', () => {
  // ⚠️ **Filtered rather than counted, and this is the case that proves it.** One unlabelled row among ninety-nine Indian
  // ones would otherwise make the country *vary* — and print India a hundred times, which is the exact outcome the rule
  // exists to prevent.
  assert.equal(varies(['in', 'in', '']), false);
  assert.equal(varies(['', '']), false);
  assert.equal(varies(['in', 'bd', '']), true);
});

test('a code the table does not know prints as itself', () => {
  // ⚠️ The same degrade `genreLabel` keeps, for the same reason: a vocabulary that grows should look wrong **visibly**
  // rather than put `undefined` on a slide.
  assert.equal(countryLabel('in', EN), 'India');
  assert.equal(countryLabel('nz', EN), 'nz');
  assert.equal(languageLabel('bn', EN), 'Bengali');
  assert.equal(languageLabel('xx', EN), 'xx');
});

test('the English chart names the countries its international lists are in', () => {
  // ⚠️ **2026-10-15** — the chart reads `us`, `gb`, `ca` and `au` lists, so ticket 20's country label now draws on it and
  // these are the words it prints. ⚠️ `nz` is deliberately **not** in the table, which is what the test above asserts.
  assert.equal(countryLabel('us', EN), 'US');
  assert.equal(countryLabel('gb', EN), 'UK');
  assert.equal(countryLabel('ca', EN), 'Canada');
  assert.equal(countryLabel('au', EN), 'Australia');
  // ⚠️ **And the market sentence follows the sources**: `worldwide`, not `us`.
  assert.equal(EN.markets.worldwide, 'Worldwide');
  // ⚠️ **`us` is kept** even though no chart declares it any more — a week committed before the change still carries it,
  // and ADR 0003 promises a past week re-renders with **today's** words.
  assert.equal(EN.markets.us, 'US lists');
});

test('the Bengali table names the countries and languages in Bengali', () => {
  // ⚠️ **Authored, not transliterated** — the split `markets` already makes. The Bengali chart is the one chart where the
  // country label draws, so this is the table a reader actually meets.
  const bn = tableFor('bn');

  assert.equal(countryLabel('bd', bn), 'বাংলাদেশ');
  assert.equal(languageLabel('hi', bn), 'হিন্দি');
});

