/**
 * Lightweight shim so AgentTaskRunner doesn't need react-markdown installed.
 * Renders markdown-like content using basic formatting.
 * Safe: never executes scripts, uses dangerouslySetInnerHTML only for
 * simple replacements with no user-executable content.
 */

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function markdownToHtml(md) {
  let html = escapeHtml(md);

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold mt-3 mb-1">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold mt-4 mb-1">$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1 class="text-xl font-bold mt-4 mb-2">$1</h1>');

  // Bold & italic
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  html = html.replace(/`(.+?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">$1</code>');

  // Bullet lists
  html = html.replace(/^[-*] (.+)$/gm, '<li class="ml-4 list-disc">$1</li>');
  html = html.replace(/(<li[\s\S]*?<\/li>)/g, '<ul class="space-y-0.5 my-1">$1</ul>');

  // Numbered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>');

  // Horizontal rule
  html = html.replace(/^---$/gm, '<hr class="my-3 border-gray-200" />');

  // Newlines to paragraphs (double newlines)
  html = html.replace(/\n\n/g, '</p><p class="mb-2">');
  html = '<p class="mb-2">' + html + '</p>';

  // Single newlines
  html = html.replace(/\n/g, '<br />');

  return html;
}

export default function ReactMarkdownShim({ children }) {
  if (!children) return null;
  const html = markdownToHtml(String(children));
  return (
    <div
      className="prose prose-sm max-w-none text-gray-800 leading-relaxed"
      // Safe: no user-executed scripts, only pre-escaped text with formatting tags
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
