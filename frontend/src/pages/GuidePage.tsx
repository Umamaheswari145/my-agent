import PageContainer from '../components/PageContainer';
import PageHeader from '../components/PageHeader';
import { BookIcon } from '../components/Icons';
import guideText from '../content/guide.txt?raw';

const sections = guideText.trim().split(/\n\s*\n/).map((block) => {
  const [heading, ...lines] = block.split('\n');
  return { heading, lines };
});

export default function GuidePage() {
  return (
    <PageContainer>
        <PageHeader
          title="Guide"
          description="Quick steps and instructions loaded from guide.txt."
          action={<BookIcon className="h-8 w-8 text-sky-500" />}
        />

        <div className="space-y-4">
          {sections.map((section) => (
            <section
              key={section.heading}
              className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
            >
              <h2 className="text-base font-semibold">{section.heading}</h2>
              <div className="mt-2 space-y-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {section.lines.map((line, index) =>
                  line.startsWith('- ') ? (
                    <p key={index} className="flex gap-2">
                      <span className="text-sky-500">•</span>
                      <span>{line.slice(2)}</span>
                    </p>
                  ) : (
                    <p key={index}>{line}</p>
                  ),
                )}
              </div>
            </section>
          ))}
        </div>
    </PageContainer>
  );
}
