// Counts the words, lines and characters in a text. Reads one JSON object on stdin, prints one on stdout.
//
// Input:  {"text": "hello there\nworld"}
// Output: {"words": 3, "lines": 2, "characters": 17, "text": "3 words, 2 lines, 17 characters"}  or  {"error": "..."}

let text: unknown;
try {
  text = JSON.parse(await new Response(Deno.stdin.readable).text()).text;
} catch {
  text = undefined;
}

if (typeof text !== "string") {
  console.log(JSON.stringify({ error: "Give text as a string." }));
} else {
  const words = text.split(/\s+/).filter(Boolean).length;
  const lines = text === "" ? 0 : text.split(/\r\n|\r|\n/).length - (/(\r\n|\r|\n)$/.test(text) ? 1 : 0);
  const characters = [...text].length;
  console.log(JSON.stringify({ words, lines, characters, text: `${words} words, ${lines} lines, ${characters} characters` }));
}
