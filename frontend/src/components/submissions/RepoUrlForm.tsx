import { Input, Stack, Text } from '@chakra-ui/react';
import { useState, type FormEvent } from 'react';
import { GradientButton } from '../ui/GradientButton';

const REPO_REGEX = /^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/;

function isValidRepoUrl(url: string): boolean {
  return REPO_REGEX.test(url.trim());
}

interface RepoUrlFormProps {
  onSubmit: (repoUrl: string, title?: string) => Promise<void>;
  submitting: boolean;
  serverError: string | null;
}

export function RepoUrlForm({ onSubmit, submitting, serverError }: RepoUrlFormProps) {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [touched, setTouched] = useState(false);

  const urlError = touched && !isValidRepoUrl(url) ? 'Enter a URL like https://github.com/owner/repo' : null;

  const handleSubmit = (e: FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    setTouched(true);
    if (!isValidRepoUrl(url)) return;
    const trimmedTitle = title.trim();
    void onSubmit(url.trim(), trimmedTitle.length > 0 ? trimmedTitle : undefined);
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <Stack gap={4}>
        <Stack gap={1}>
          <Text fontWeight="semibold">GitHub repository URL</Text>
          <Input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onBlur={() => setTouched(true)}
            placeholder="https://github.com/owner/repo"
            aria-invalid={urlError !== null}
          />
          {urlError && (
            <Text color="red.300" fontSize="sm">
              {urlError}
            </Text>
          )}
        </Stack>
        <Stack gap={1}>
          <Text fontWeight="semibold">Assignment title (optional)</Text>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Week 3 - Todo App" maxLength={200} />
        </Stack>
        {serverError && <Text color="red.300">{serverError}</Text>}
        <GradientButton type="submit" disabled={submitting} opacity={submitting ? 0.6 : 1}>
          {submitting ? 'Submitting...' : 'Roast my code'}
        </GradientButton>
      </Stack>
    </form>
  );
}
