import type { ReactNode } from "react";

type Block =
  | { type: "heading"; level: 1 | 2 | 3; content: string }
  | { type: "paragraph"; content: string }
  | { type: "fact"; label: string; value: string }
  | { type: "unordered"; items: string[] }
  | { type: "ordered"; items: string[] }
  | { type: "divider" };

const factPattern = /^([A-Za-zÀ-ÿ0-9 /+&()._-]{2,34}):\s+(.+)$/;
const unorderedPattern = /^[-*•]\s+(.+)$/;
const orderedPattern = /^\d+[.)]\s+(.+)$/;

function inline(content: string): ReactNode[] {
  const tokens = content.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);

  return tokens.map((token, index) => {
    if (token.startsWith("**") && token.endsWith("**")) {
      return <strong key={`${token}-${index}`}>{token.slice(2, -2)}</strong>;
    }

    if (token.startsWith("`") && token.endsWith("`")) {
      return <code key={`${token}-${index}`}>{token.slice(1, -1)}</code>;
    }

    return <span key={`${token}-${index}`}>{token}</span>;
  });
}

function parse(content: string): Block[] {
  const normalized = content.replace(/\r\n/g, "\n").trim();
  if (!normalized) return [];

  const lines = normalized.split("\n");
  const blocks: Block[] = [];
  let paragraph: string[] = [];
  let unordered: string[] = [];
  let ordered: string[] = [];

  function flushParagraph() {
    if (!paragraph.length) return;
    blocks.push({ type: "paragraph", content: paragraph.join(" ").trim() });
    paragraph = [];
  }

  function flushLists() {
    if (unordered.length) {
      blocks.push({ type: "unordered", items: unordered });
      unordered = [];
    }
    if (ordered.length) {
      blocks.push({ type: "ordered", items: ordered });
      ordered = [];
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      flushParagraph();
      flushLists();
      continue;
    }

    if (/^---+$/.test(line)) {
      flushParagraph();
      flushLists();
      blocks.push({ type: "divider" });
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      flushLists();
      blocks.push({
        type: "heading",
        level: Math.min(3, heading[1].length) as 1 | 2 | 3,
        content: heading[2],
      });
      continue;
    }

    const unorderedMatch = line.match(unorderedPattern);
    if (unorderedMatch) {
      flushParagraph();
      if (ordered.length) flushLists();
      unordered.push(unorderedMatch[1]);
      continue;
    }

    const orderedMatch = line.match(orderedPattern);
    if (orderedMatch) {
      flushParagraph();
      if (unordered.length) flushLists();
      ordered.push(orderedMatch[1]);
      continue;
    }

    const factMatch = line.match(factPattern);
    if (factMatch && !line.startsWith("http")) {
      flushParagraph();
      flushLists();
      blocks.push({ type: "fact", label: factMatch[1], value: factMatch[2] });
      continue;
    }

    paragraph.push(line);
  }

  flushParagraph();
  flushLists();

  return blocks;
}

export default function RichMessage({
  content,
  compact = false,
}: {
  content: string;
  compact?: boolean;
}) {
  const blocks = parse(content);

  if (!blocks.length) return null;

  return (
    <div className={`rich-message ${compact ? "rich-message--compact" : ""}`}>
      {blocks.map((block, index) => {
        if (block.type === "heading") {
          const className = `rich-message__heading rich-message__heading--${block.level}`;
          return <div className={className} key={`heading-${index}`}>{inline(block.content)}</div>;
        }

        if (block.type === "paragraph") {
          return <p key={`paragraph-${index}`}>{inline(block.content)}</p>;
        }

        if (block.type === "fact") {
          return (
            <div className="rich-message__fact" key={`fact-${index}`}>
              <span>{block.label}</span>
              <b>{inline(block.value)}</b>
            </div>
          );
        }

        if (block.type === "unordered") {
          return (
            <ul key={`unordered-${index}`}>
              {block.items.map((item, itemIndex) => (
                <li key={`${item}-${itemIndex}`}>
                  <i />
                  <span>{inline(item)}</span>
                </li>
              ))}
            </ul>
          );
        }

        if (block.type === "ordered") {
          return (
            <ol key={`ordered-${index}`}>
              {block.items.map((item, itemIndex) => (
                <li key={`${item}-${itemIndex}`}>
                  <span className="rich-message__number">{itemIndex + 1}</span>
                  <span>{inline(item)}</span>
                </li>
              ))}
            </ol>
          );
        }

        return <hr key={`divider-${index}`} />;
      })}
    </div>
  );
}
