import JobDetailClient from './JobDetailClient';

export const dynamicParams = false; // Required for static export

// Generate placeholder for static export
export function generateStaticParams() {
  return [{ id: 'placeholder' }];
}

export default function JobDetailPage({ params }: { params: { id: string } }) {
  return <JobDetailClient params={params} />;
}