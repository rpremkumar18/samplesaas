import { Heading, Text } from '@chakra-ui/react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { RepoUrlForm } from '../components/submissions/RepoUrlForm';
import { createSubmission, extractErrorMessage } from '../services/submissionService';

export default function NewSubmissionPage() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (repoUrl: string, title?: string): Promise<void> => {
    setSubmitting(true);
    setError(null);
    try {
      const created = await createSubmission({ repo_url: repoUrl, assignment_title: title });
      navigate(`/submissions/${created.id}`);
    } catch (e: unknown) {
      setError(extractErrorMessage(e, 'Could not submit that repository.'));
      setSubmitting(false);
    }
  };

  return (
    <PageWrapper>
      <Heading size="2xl" mb={2}>
        New submission
      </Heading>
      <Text color="gray.400" mb={6}>
        Paste a public GitHub repo and prepare to be roasted.
      </Text>
      <GlassCard maxW="2xl">
        <RepoUrlForm onSubmit={handleSubmit} submitting={submitting} serverError={error} />
      </GlassCard>
    </PageWrapper>
  );
}
