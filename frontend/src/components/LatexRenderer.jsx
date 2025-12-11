import { InlineMath, BlockMath } from 'react-katex';
import 'katex/dist/katex.min.css';
import { useMemo } from 'react';

export default function LatexRenderer({ text, className = '', inline = false }) {
  const renderedContent = useMemo(() => {
    if (!text) return null;

    const parts = [];
    let lastIndex = 0;
    let key = 0;

    const blockRegex = /\$\$(.*?)\$\$/g;
    const inlineRegex = /\$(.*?)\$/g;

    const blockMatches = [...text.matchAll(blockRegex)];
    const inlineMatches = [...text.matchAll(inlineRegex)];

    const allMatches = [
      ...blockMatches.map(m => ({ match: m, type: 'block' })),
      ...inlineMatches.map(m => ({ match: m, type: 'inline' }))
    ].sort((a, b) => a.match.index - b.match.index);

    const processedRanges = new Set();

    allMatches.forEach(({ match, type }) => {
      const start = match.index;
      const end = start + match[0].length;

      if ([...processedRanges].some(range =>
        (start >= range.start && start < range.end) ||
        (end > range.start && end <= range.end)
      )) {
        return;
      }

      if (start > lastIndex) {
        const textBefore = text.substring(lastIndex, start);
        if (textBefore) {
          parts.push(
            <span key={`text-${key++}`}>
              {textBefore}
            </span>
          );
        }
      }

      const latex = match[1];

      if (type === 'block') {
        parts.push(
          <div key={`block-${key++}`} className="my-2">
            <BlockMath math={latex} />
          </div>
        );
        processedRanges.add({ start: start, end: end });
      } else {
        parts.push(
          <InlineMath key={`inline-${key++}`} math={latex} />
        );
        processedRanges.add({ start: start, end: end });
      }

      lastIndex = end;
    });

    if (lastIndex < text.length) {
      const textAfter = text.substring(lastIndex);
      if (textAfter) {
        parts.push(
          <span key={`text-${key++}`}>
            {textAfter}
          </span>
        );
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
