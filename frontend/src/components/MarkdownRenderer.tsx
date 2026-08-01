"use client";

import { type ReactNode } from "react";

/**
 * Lightweight markdown renderer — no external deps.
 * Supports: ## headers, **bold**, *italic*, - lists, `code`, ```code blocks```, paragraphs.
 */
export function MarkdownRenderer({ content }: { content: string }) {
  const blocks = parseBlocks(content);
  return (
    <div style={{ fontFamily: "var(--fontSans)", fontSize: "0.875rem", lineHeight: 1.7, color: "var(--text)" }}>
      {blocks.map((block, i) => renderBlock(block, i))}
    </div>
  );
}

interface Block {
  type: "h1" | "h2" | "h3" | "p" | "ul" | "ol" | "code" | "hr";
  content?: string;
  items?: string[];
  lang?: string;
}

function parseBlocks(text: string): Block[] {
  const lines = text.split("\n");
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Code block
    if (line.trim().startsWith("```")) {
      const lang = line.trim().slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      blocks.push({ type: "code", content: codeLines.join("\n"), lang });
      continue;
    }

    // Horizontal rule
    if (line.trim() === "---" || line.trim() === "___") {
      blocks.push({ type: "hr" });
      i++;
      continue;
    }

    // Headers
    const headerMatch = line.match(/^(#{1,3})\s+(.*)/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      blocks.push({
        type: level === 1 ? "h1" : level === 2 ? "h2" : "h3",
        content: headerMatch[2],
      });
      i++;
      continue;
    }

    // Unordered list
    if (line.match(/^\s*[-*]\s+/)) {
      const items: string[] = [];
      while (i < lines.length && lines[i].match(/^\s*[-*]\s+/)) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    // Ordered list
    if (line.match(/^\s*\d+\.\s+/)) {
      const items: string[] = [];
      while (i < lines.length && lines[i].match(/^\s*\d+\.\s+/)) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i++;
      }
      blocks.push({ type: "ol", items });
      continue;
    }

    // Paragraph (accumulate until blank line or block change)
    if (line.trim() === "") {
      i++;
      continue;
    }

    const paraLines: string[] = [];
    while (i < lines.length && lines[i].trim() !== "" &&
           !lines[i].trim().startsWith("```") &&
           !lines[i].trim().startsWith("#") &&
           !lines[i].match(/^\s*[-*]\s+/) &&
           !lines[i].match(/^\s*\d+\.\s+/) &&
           lines[i].trim() !== "---") {
      paraLines.push(lines[i]);
      i++;
    }
    blocks.push({ type: "p", content: paraLines.join(" ") });
  }

  return blocks;
}

function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // Bold + italic ***text***
    let match = remaining.match(/\*\*\*(.+?)\*\*\*/);
    if (match) {
      const idx = remaining.indexOf(match[0]);
      if (idx > 0) nodes.push(remaining.slice(0, idx));
      nodes.push(<strong key={key++} style={{ fontWeight: 700 }}><em>{match[1]}</em></strong>);
      remaining = remaining.slice(idx + match[0].length);
      continue;
    }

    // Bold **text**
    match = remaining.match(/\*\*(.+?)\*\*/);
    if (match) {
      const idx = remaining.indexOf(match[0]);
      if (idx > 0) nodes.push(remaining.slice(0, idx));
      nodes.push(<strong key={key++} style={{ fontWeight: 700 }}>{match[1]}</strong>);
      remaining = remaining.slice(idx + match[0].length);
      continue;
    }

    // Italic *text*
    match = remaining.match(/\*(.+?)\*/);
    if (match) {
      const idx = remaining.indexOf(match[0]);
      if (idx > 0) nodes.push(remaining.slice(0, idx));
      nodes.push(<em key={key++}>{match[1]}</em>);
      remaining = remaining.slice(idx + match[0].length);
      continue;
    }

    // Inline code `text`
    match = remaining.match(/`(.+?)`/);
    if (match) {
      const idx = remaining.indexOf(match[0]);
      if (idx > 0) nodes.push(remaining.slice(0, idx));
      nodes.push(
        <code key={key++} style={{
          background: "var(--code)",
          padding: "0.125rem 0.375rem",
          borderRadius: "4px",
          fontFamily: "var(--fontMono)",
          fontSize: "0.8125rem",
          color: "var(--accent)",
        }}>
          {match[1]}
        </code>
      );
      remaining = remaining.slice(idx + match[0].length);
      continue;
    }

    // No more matches
    nodes.push(remaining);
    break;
  }

  return nodes;
}

function renderBlock(block: Block, key: number): ReactNode {
  switch (block.type) {
    case "h1":
      return (
        <h3 key={key} style={{
          fontFamily: "var(--fontSerif)",
          fontSize: "1.25rem",
          fontWeight: 600,
          color: "var(--primary)",
          margin: "0.75rem 0 0.5rem",
        }}>
          {renderInline(block.content || "")}
        </h3>
      );
    case "h2":
      return (
        <h4 key={key} style={{
          fontFamily: "var(--fontSerif)",
          fontSize: "1.0625rem",
          fontWeight: 600,
          color: "var(--primary)",
          margin: "0.625rem 0 0.375rem",
        }}>
          {renderInline(block.content || "")}
        </h4>
      );
    case "h3":
      return (
        <h5 key={key} style={{
          fontFamily: "var(--fontSerif)",
          fontSize: "0.9375rem",
          fontWeight: 600,
          color: "var(--primary)",
          margin: "0.5rem 0 0.25rem",
        }}>
          {renderInline(block.content || "")}
        </h5>
      );
    case "p":
      return (
        <p key={key} style={{ margin: "0.375rem 0" }}>
          {renderInline(block.content || "")}
        </p>
      );
    case "ul":
      return (
        <ul key={key} style={{ margin: "0.375rem 0", paddingLeft: "1.25rem", listStyle: "disc" }}>
          {block.items?.map((item, i) => (
            <li key={i} style={{ margin: "0.125rem 0" }}>{renderInline(item)}</li>
          ))}
        </ul>
      );
    case "ol":
      return (
        <ol key={key} style={{ margin: "0.375rem 0", paddingLeft: "1.25rem", listStyle: "decimal" }}>
          {block.items?.map((item, i) => (
            <li key={i} style={{ margin: "0.125rem 0" }}>{renderInline(item)}</li>
          ))}
        </ol>
      );
    case "code":
      return (
        <pre key={key} style={{
          background: "#1e1e1e",
          color: "#d4d4d4",
          borderRadius: "8px",
          padding: "0.75rem",
          margin: "0.5rem 0",
          overflowX: "auto",
          fontFamily: "var(--fontMono)",
          fontSize: "0.8125rem",
          lineHeight: 1.5,
        }}>
          <code>{block.content}</code>
        </pre>
      );
    case "hr":
      return <hr key={key} style={{ border: "none", borderTop: "1px solid var(--border)", margin: "0.75rem 0" }} />;
    default:
      return null;
  }
}
