const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {test} = require('node:test');
const path = require('node:path');
const web = path.resolve(__dirname, '../web');
const workspace = path.join(web, 'chat/workspace.js');
const source = fs.readFileSync(fs.existsSync(workspace) ? workspace : path.join(web, 'dashboard.js'), 'utf8');
function chatFunction(name, next) {
  return source.slice(source.indexOf('async function '+name), source.indexOf('function '+next));
}
test('attachments stay with the conversation selected before the upload', async () => {
  let resolveRead;
  const sent = [];
  const context = vm.createContext({
    activeChatId: 'first', pendingAttachments: [], uploadingChatFiles: false,
    el: () => ({}), renderPendingFiles() {}, renderChatHeaderStatus() {}, toast() {},
    fileToBase64: () => new Promise(resolve => {resolveRead = resolve;}),
    post: async (_, payload) => {sent.push(payload); return {id: 'attachment'};}
  });
  vm.runInContext(chatFunction('handleChatFiles', 'fileToBase64'), context);
  const upload = context.handleChatFiles([{name: 'notes.txt', size: 10}]);
  context.activeChatId = 'second';
  resolveRead('example');
  await upload;
  assert.equal(sent[0].conversation, 'first');
  assert.equal(context.pendingAttachments.length, 0);
});
