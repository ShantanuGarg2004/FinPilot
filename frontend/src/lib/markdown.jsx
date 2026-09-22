/* Lightweight markdown renderer used for AI advisory + chat responses.
   Ported from the original single-file app and re-themed to the FinPilot
   navy/emerald palette. */

function escHtml(t) {
  return t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function inlineMd(text) {
  if (!text) return "";
  return escHtml(text)
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "<span style='color:#18B981'>$1</span>")
    .replace(/\*{3}(.+?)\*{3}/g, "<strong><em>$1</em></strong>")
    .replace(/\*{2}(.+?)\*{2}/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/__(.+?)__/g, "<strong>$1</strong>")
    .replace(/_([^_]+)_/g, "<em>$1</em>")
    .replace(
      /`([^`]+)`/g,
      "<code style='background:rgba(24,185,129,0.12);color:#18B981;padding:1px 5px;border-radius:4px;font-size:0.9em'>$1</code>"
    )
    .replace(/~~(.+?)~~/g, "<s>$1</s>");
}

function parseMarkdown(md) {
  if (!md) return "";
  const lines = md.split("\n");
  const out = [];
  let i = 0;

  while (i < lines.length) {
    const raw = lines[i];
    const s = raw.trim();

    // Fenced code block
    if (/^(`{3,}|~{3,})/.test(s)) {
      const fence = s.match(/^(`{3,}|~{3,})/)[0];
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith(fence)) {
        codeLines.push(lines[i]);
        i++;
      }
      out.push(
        `<pre style="background:#050505;border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:14px 16px;overflow-x:auto;margin:12px 0"><code style="font-family:monospace;font-size:12.5px;color:#18B981;line-height:1.7">${escHtml(
          codeLines.join("\n")
        )}</code></pre>`
      );
      i++;
      continue;
    }

    // Horizontal rule
    if (/^([-*_]){3,}$/.test(s)) {
      out.push('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:16px 0"/>');
      i++;
      continue;
    }

    // Heading
    const hm = s.match(/^(#{1,4})\s+(.*)/);
    if (hm) {
      const lvl = hm[1].length;
      const sizes = ["1.3em", "1.15em", "1.05em", "1em"];
      const margins = ["18px 0 8px", "14px 0 6px", "12px 0 5px", "10px 0 4px"];
      const colors = ["#F4F7FB", "#18B981", "#9AA8BC", "#9AA8BC"];
      out.push(
        `<h${lvl} style="font-size:${sizes[lvl - 1]};margin:${margins[lvl - 1]};color:${
          colors[lvl - 1]
        };font-family:'Manrope',sans-serif;font-weight:600;letter-spacing:-0.01em">${inlineMd(hm[2])}</h${lvl}>`
      );
      if (lvl <= 2)
        out.push('<div style="height:1px;background:rgba(255,255,255,0.06);margin-bottom:8px"></div>');
      i++;
      continue;
    }

    // Blockquote
    if (/^>/.test(s)) {
      const bqLines = [];
      while (i < lines.length && /^>/.test(lines[i].trim())) {
        bqLines.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }
      out.push(
        `<blockquote style="border-left:3px solid #18B981;margin:10px 0;padding:8px 14px;background:rgba(24,185,129,0.08);border-radius:0 6px 6px 0;color:#9AA8BC;font-size:13px;line-height:1.7">${bqLines
          .map((l) => inlineMd(l))
          .join("<br/>")}</blockquote>`
      );
      continue;
    }

    // GFM table
    if (s.includes("|") && !/^[\s|:-]+$/.test(s)) {
      const tblLines = [];
      while (i < lines.length && lines[i].includes("|")) {
        tblLines.push(lines[i]);
        i++;
      }
      if (tblLines.length >= 2) {
        const parseCells = (row) => {
          const parts = row.split("|").map((c) => c.trim());
          return parts[0] === ""
            ? parts.slice(1, parts[parts.length - 1] === "" ? -1 : undefined)
            : parts;
        };
        const hdrs = parseCells(tblLines[0]);
        const rows = tblLines.slice(2).map(parseCells);
        let t = `<div style="overflow-x:auto;margin:12px 0"><table style="width:100%;border-collapse:collapse;font-size:13px"><thead><tr>`;
        hdrs.forEach((h) => {
          t += `<th style="padding:8px 12px;text-align:left;color:#18B981;border-bottom:1px solid rgba(24,185,129,0.2);font-weight:600;background:rgba(24,185,129,0.08)">${inlineMd(
            h
          )}</th>`;
        });
        t += `</tr></thead><tbody>`;
        rows.forEach((row, ri) => {
          t += `<tr style="background:${ri % 2 ? "rgba(255,255,255,0.01)" : "transparent"}">`;
          hdrs.forEach((_, ci) => {
            t += `<td style="padding:7px 12px;color:#9AA8BC;border-bottom:1px solid rgba(255,255,255,0.04)">${inlineMd(
              row[ci] || ""
            )}</td>`;
          });
          t += "</tr>";
        });
        t += `</tbody></table></div>`;
        out.push(t);
        continue;
      }
    }

    // Table separator leftover
    if (/^[\s|:-]+$/.test(s) && s.includes("|")) {
      i++;
      continue;
    }

    // Unordered list
    if (/^(\s*)[-*+]\s+/.test(raw)) {
      const items = [];
      while (i < lines.length && /^(\s*)[-*+]\s+/.test(lines[i])) {
        const depth = Math.floor(lines[i].match(/^(\s*)/)[1].length / 2);
        items.push({ depth, text: lines[i].replace(/^\s*[-*+]\s+/, "") });
        i++;
      }
      let l = `<ul style="margin:8px 0;padding-left:0;list-style:none">`;
      items.forEach(({ depth, text }) => {
        l += `<li style="display:flex;align-items:flex-start;gap:8px;padding:3px 0;padding-left:${
          depth * 16
        }px;color:#9AA8BC;font-size:13px;line-height:1.65"><span style="color:#18B981;margin-top:6px;flex-shrink:0;font-size:7px">●</span><span>${inlineMd(
          text
        )}</span></li>`;
      });
      l += `</ul>`;
      out.push(l);
      continue;
    }

    // Ordered list
    if (/^(\s*)\d+[.)]\s+/.test(raw)) {
      const items = [];
      const counter = {};
      while (i < lines.length && /^(\s*)\d+[.)]\s+/.test(lines[i])) {
        const depth = Math.floor(lines[i].match(/^(\s*)/)[1].length / 2);
        counter[depth] = (counter[depth] || 0) + 1;
        items.push({ depth, text: lines[i].replace(/^\s*\d+[.)]\s+/, ""), num: counter[depth] });
        i++;
      }
      let l = `<ol style="margin:8px 0;padding-left:0;list-style:none">`;
      items.forEach(({ depth, text, num }) => {
        l += `<li style="display:flex;align-items:flex-start;gap:10px;padding:4px 0;padding-left:${
          depth * 16
        }px;color:#9AA8BC;font-size:13px;line-height:1.65"><span style="color:#18B981;font-weight:600;font-size:12px;flex-shrink:0;min-width:18px;padding-top:1px">${num}.</span><span>${inlineMd(
          text
        )}</span></li>`;
      });
      l += `</ol>`;
      out.push(l);
      continue;
    }

    // Blank line
    if (!s) {
      out.push('<div style="height:6px"></div>');
      i++;
      continue;
    }

    // Paragraph
    out.push(
      `<p style="margin:4px 0 8px;color:#9AA8BC;font-size:13px;line-height:1.75">${inlineMd(s)}</p>`
    );
    i++;
  }

  return out.join("\n");
}

export default function MarkdownRenderer({ content }) {
  const html = parseMarkdown(content || "");
  return <div className="md-body" dangerouslySetInnerHTML={{ __html: html }} />;
}
