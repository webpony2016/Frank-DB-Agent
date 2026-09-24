import test from 'node:test';
import assert from 'node:assert/strict';
import * as ui from '../app/static/api.js';

test('saving a note identifies unsaved quote edits', () => {
  assert.deepEqual(ui.findUnsavedForms([
    {key: 'quote', label: 'Quote', before: [['quantity', '1']], after: [['quantity', '999']]},
    {key: 'note', label: 'Operational note', before: [['text', '']], after: [['text', 'Access instruction']]},
  ], 'note'), ['Quote']);
});
test('saving a note identifies unsaved customer message edits', () => {
  assert.deepEqual(ui.findUnsavedForms([
    {key: 'message', label: 'Customer update draft', before: [['body', 'Original']], after: [['body', 'Edited']]},
  ], 'note'), ['Customer update draft']);
});
test('submitted and restored forms require no discard decision', () => {
  assert.deepEqual(ui.findUnsavedForms([
    {key: 'quote', label: 'Quote', before: [['quantity', '1']], after: [['quantity', '2']]},
    {key: 'message', label: 'Message', before: [['body', 'Original']], after: [['body', 'Original']]},
  ], 'quote'), []);
});
test('added quote lines are unsaved even when field names repeat', () => {
  assert.deepEqual(ui.findUnsavedForms([
    {key: 'quote', label: 'Quote', before: [['quantity', '1']], after: [['quantity', '1'], ['quantity', '1']]},
  ], null), ['Quote']);
});
test('overview activity stays limited to eight newest entries', () => {
  assert.deepEqual(ui.activityWindow(Array.from({length: 10}, (_, i) => i)), [9, 8, 7, 6, 5, 4, 3, 2]);
});
test('expanded activity includes old notes without reordering source data', () => {
  const events = ['Old site instruction', ...Array.from({length: 9}, (_, i) => 'Update ' + i)];
  assert.equal(ui.activityWindow(events, null).at(-1), 'Old site instruction');
  assert.equal(events[0], 'Old site instruction');
  assert.equal(ui.activityWindow(events, null).length, 10);
});
