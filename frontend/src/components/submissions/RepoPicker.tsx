import { Badge, Box, Button, Input, Spinner, Stack, Text } from '@chakra-ui/react';
import { useMemo, useState, type FormEvent } from 'react';
import type { GitHubRepo } from '../../types';
import { GradientButton } from '../ui/GradientButton';

interface RepoPickerProps {
  repos: GitHubRepo[];
  loading: boolean;
  error: string | null;
  onSubmit: (repoUrl: string, title?: string) => Promise<void>;
  submitting: boolean;
  serverError: string | null;
}

export function RepoPicker({ repos, loading, error, onSubmit, submitting, serverError }: RepoPickerProps) {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<GitHubRepo | null>(null);
  const [title, setTitle] = useState('');

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? repos.filter((r) => r.name.toLowerCase().includes(q)) : repos;
  }, [repos, query]);

  const handleSubmit = (e: FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    if (!selected) return;
    const trimmed = title.trim();
    void onSubmit(selected.html_url, trimmed.length > 0 ? trimmed : undefined);
  };

  if (loading) return <Spinner aria-label="Loading repositories" />;
  if (error) return <Text color="fg.error">{error}</Text>;

  const blocked = !selected || submitting;

  return (
    <form onSubmit={handleSubmit} noValidate>
      <Stack gap={4}>
        <Text fontWeight="semibold">Pick one of your public repositories</Text>
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search your repositories"
          aria-label="Search repositories"
        />
        {repos.length === 0 ? (
          <Text color="fg.muted">No public repositories found on your GitHub account.</Text>
        ) : (
          <Stack gap={2} maxH="22rem" overflowY="auto">
            {visible.map((repo) => (
              <Button
                key={repo.html_url}
                type="button"
                variant={selected?.html_url === repo.html_url ? 'solid' : 'outline'}
                justifyContent="flex-start"
                h="auto"
                py={3}
                onClick={() => setSelected(repo)}
                aria-pressed={selected?.html_url === repo.html_url}
              >
                <Box textAlign="left">
                  <Text fontWeight="semibold">{repo.name}</Text>
                  {repo.description && (
                    <Text fontSize="sm" fontWeight="normal" color="fg.muted">
                      {repo.description}
                    </Text>
                  )}
                </Box>
                {repo.language && <Badge ml="auto">{repo.language}</Badge>}
              </Button>
            ))}
            {visible.length === 0 && <Text color="fg.muted">No repositories match that search.</Text>}
          </Stack>
        )}
        <Stack gap={1}>
          <Text fontWeight="semibold">Assignment title (optional)</Text>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Week 3 - Todo App"
            maxLength={200}
          />
        </Stack>
        {serverError && <Text color="fg.error">{serverError}</Text>}
        <GradientButton type="submit" disabled={blocked} opacity={blocked ? 0.6 : 1}>
          {submitting ? 'Submitting...' : selected ? `Roast ${selected.name}` : 'Select a repository'}
        </GradientButton>
      </Stack>
    </form>
  );
}
