import http from 'node:http';
import { readFile } from 'node:fs/promises';

const instructions = 'Sort the support message into one category: billing, bug, account or other. Reply with the category only.';
const model = process.env.MUBIT_MODEL || 'gpt-6-luna';
const key = process.env.MUBIT_API_KEY;
const categories = ['billing', 'bug', 'account', 'other'];
const page = await readFile(new URL('./index.html', import.meta.url));
const port = Number(process.env.PORT || 3000);
const origin = `http://localhost:${port}`;
let busy = false;

function json(res, status, data) {
  res.writeHead(status, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(data));
}

http.createServer(async (req, res) => {
  if (req.method === 'GET' && req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    return res.end(page);
  }
  if (req.method === 'GET' && req.url === '/api/config') {
    return json(res, 200, { mode: key ? 'live' : 'demo', model, instructions });
  }
  if (req.method !== 'POST' || req.url !== '/api/classify') return json(res, 404, { error: 'Not found' });
  if (req.headers.origin !== origin || !req.headers['content-type']?.startsWith('application/json')) {
    return json(res, 403, { error: 'Open the app at ' + origin });
  }
  if (busy) return json(res, 429, { error: 'A request is already running. Try again when it finishes.' });
  busy = true;
  try {
    let body = '';
    for await (const chunk of req) {
      body += chunk;
      if (Buffer.byteLength(body) > 12000) {
        json(res, 413, { error: 'Message is too long.' });
        return;
      }
    }
    let input;
    try { input = JSON.parse(body); } catch { return json(res, 400, { error: 'Invalid request.' }); }
    const message = input.message;
    if (typeof message !== 'string' || !message.trim() || message.length > 4000) {
      return json(res, 400, { error: 'Enter a message of 1–4000 characters.' });
    }
    if (!key) {
      const category = /charge|refund|invoice|payment/i.test(message) ? 'billing' : /crash|error|broken|bug/i.test(message) ? 'bug' : /password|sign in|email|account/i.test(message) ? 'account' : 'other';
      return json(res, 200, { category, mode: 'demo', duration: 0 });
    }
    const start = performance.now();
    const response = await fetch('https://api.mubit.ai/openai/v1/chat/completions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, messages: [{ role: 'system', content: instructions }, { role: 'user', content: message }], metadata: { session_id: crypto.randomUUID() } }),
      signal: AbortSignal.timeout(90000),
    });
    const requestId = response.headers.get('x-middleware-request-id');
    if (!response.ok) return json(res, 502, { error: `Mubit returned HTTP ${response.status}. Check your key, provider access, and model in the console.`, requestId });
    const data = await response.json();
    const answer = data.choices?.[0]?.message?.content;
    if (typeof answer !== 'string') return json(res, 502, { error: 'The provider returned no text answer.', requestId });
    const category = answer.trim().toLowerCase();
    return json(res, 200, { category: categories.includes(category) ? category : 'Unexpected output', answer, mode: 'live', duration: Math.round(performance.now() - start), requestId, usage: data.usage });
  } catch (error) {
    json(res, 502, { error: error.name === 'TimeoutError' ? 'Request timed out. Check Mubit Requests before retrying; the call may have been recorded.' : 'Could not complete the request. Check your connection and Mubit console.' });
  } finally { busy = false; }
}).listen(port, '127.0.0.1', () => console.log(`Mubit learning lab: ${origin} (${key ? 'live' : 'demo'} mode)`));
