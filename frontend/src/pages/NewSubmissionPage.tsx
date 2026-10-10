import { Heading, Stack, Text } from '@chakra-ui/react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { RepoPicker } from '../components/submissions/RepoPicker';
import { RepoUrlForm } from '../components/submissions/RepoUrlForm';
import { useAuth } from '../hooks/useAuth';
import { useMyRepos } from '../hooks/useMyRepos';
import { createSubmission, extractErrorMessage } from '../services/submissionService';

export default function NewSubmissionPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const hasGitHub = Boolean(user?.github_login);
  const { repos, loading, error: reposError } = useMyRepos(hasGitHub);
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
      <Text color="fg.muted" mb={6}>
        Pick a repo from your GitHub account and prepare to be roasted.
      </Text>
      <Stack gap={6} maxW="2xl">
        {hasGitHub && (
          <GlassCard>
            <RepoPicker
              repos={repos}
              loading={loading}
              error={reposError}
              onSubmit={handleSubmit}
              submitting={submitting}
              serverError={error}
            />
          </GlassCard>
        )}
        <GlassCard>
          <Text fontWeight="semibold" mb={3}>
            {hasGitHub
              ? 'Or paste any public repository URL'
              : 'Sign in with GitHub to pick from your repos, or paste a public repo URL'}
          </Text>
          <RepoUrlForm onSubmit={handleSubmit} submitting={submitting} serverError={hasGitHub ? null : error} />
        </GlassCard>
      </Stack>
    </PageWrapper>
  );
}
