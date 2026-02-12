import { InlineMath, BlockMath } from 'react-katex';
import 'katex/dist/katex.min.css';
import { useMemo } from 'react';

export default function LatexRenderer({ text, className = '', inline = false }) {
  const renderedContent = useMemo(() => {
    if (!text) return null;

    const parts = [];
    const mathRegex = /(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$)/g;
    let cursor = 0;
    let key = 0;

    for (const match of text.matchAll(mathRegex)) {
      const full = match[0];
      const start = match.index ?? 0;
      const end = start + full.length;

      if (start > cursor) {
        const plain = text.slice(cursor, start);
        if (plain) {
          parts.push(<span key={`text-${key++}`}>{plain}</span>);
        }
      }

      const isBlock = full.startsWith('$$') && full.endsWith('$$');
      const latex = isBlock ? full.slice(2, -2) : full.slice(1, -1);

      if (isBlock) {
        parts.push(
          <div key={`block-${key++}`} className="my-2">
            <BlockMath math={latex} />
          </div>
        );
      } else {
        parts.push(<InlineMath key={`inline-${key++}`} math={latex} />);
      }

      cursor = end;
    }

    if (cursor < text.length) {
      const tail = text.slice(cursor);
      if (tail) {
        parts.push(<span key={`text-${key++}`}>{tail}</span>);
      }
    }

    return parts.length > 0 ? parts : text;
  }, [text]);

  const Container = inline ? 'span' : 'div';

  return (
    <Container className={className}>
      {renderedContent}
    </Container>
  );
}
