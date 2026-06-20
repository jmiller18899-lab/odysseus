// static/js/htmlPreview.js

/**
 * Prepare arbitrary HTML for the document editor's sandboxed preview.
 *
 * LLM-generated React demos often load @babel/standalone and use
 * <script type="text/babel"> without presets. Babel then parses TSX-looking
 * snippets without TypeScript enabled and throws from babel.min.js. Add
 * conservative defaults to Babel/JSX script tags so these previews run.
 */
export function prepareHtmlPreview(html) {
  return String(html || '').replace(
    /<script\b[^>]*\btype\s*=\s*(["'])(?:text\/babel|text\/jsx)\1[^>]*>/gi,
    (tag) => withBabelDefaults(tag),
  );
}

function withBabelDefaults(tag) {
  let next = tag;

  if (/\bdata-presets\s*=/i.test(next)) {
    next = next.replace(/\bdata-presets\s*=\s*(["'])([^"']*)\1/i, (_match, quote, value) => {
      const presets = value.split(',').map((preset) => preset.trim()).filter(Boolean);
      const seen = new Set(presets.map((preset) => preset.toLowerCase()));
      for (const preset of ['env', 'react', 'typescript']) {
        if (!seen.has(preset)) presets.push(preset);
      }
      return `data-presets=${quote}${presets.join(',')}${quote}`;
    });
  } else {
    next = next.replace(/>$/, ' data-presets="env,react,typescript">');
  }

  if (!/\bdata-filename\s*=/i.test(next)) {
    next = next.replace(/>$/, ' data-filename="/preview.tsx">');
  }

  return next;
}
