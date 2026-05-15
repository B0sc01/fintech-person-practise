import katex from 'katex';
import 'katex/dist/katex.min.css';

interface Props {
  formula: string;
  displayMode?: boolean;
}

export default function MathFormula({ formula, displayMode = false }: Props) {
  if (!formula) return null;

  try {
    const html = katex.renderToString(formula, {
      displayMode,
      throwOnError: false,
      strict: false,
      trust: true,
    });
    return (
      <span
        dangerouslySetInnerHTML={{ __html: html }}
        style={displayMode ? { display: 'block', textAlign: 'center', margin: '12px 0' } : undefined}
      />
    );
  } catch {
    return <code style={{ fontSize: 13 }}>{formula}</code>;
  }
}
