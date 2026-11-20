import { Link } from 'react-router-dom';
import PageContainer from '../components/PageContainer';
import PageHeader from '../components/PageHeader';

export default function NotFoundPage() {
  return (
    <PageContainer>
      <PageHeader title="Page not found" description="That page does not exist." />
      <Link to="/" className="text-sm font-medium text-sky-600 hover:underline dark:text-sky-400">
        Return to chat
      </Link>
    </PageContainer>
  );
}
