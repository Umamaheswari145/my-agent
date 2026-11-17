import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <section className="space-y-4">
      <h1 className="text-3xl font-bold">Page not found</h1>
      <Link className="text-sky-400 hover:underline" to="/">
        Return home
      </Link>
    </section>
  );
}
