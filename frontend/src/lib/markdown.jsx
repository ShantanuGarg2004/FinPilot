import { parseMarkdown } from "./markdownText.js";

export default function MarkdownRenderer({ content }) {
  const html = parseMarkdown(content || "");
  return <div className="md-body" dangerouslySetInnerHTML={{ __html: html }} />;
}
