import { useState, type FormEvent } from 'react';
import { Stack, Text } from '@chakra-ui/react';
import { AnimatedInput } from '../ui/AnimatedInput';
import { GradientButton } from '../ui/GradientButton';
import { useAuth } from '../../hooks/useAuth';
import { getErrorMessage, updateProfile } from '../../services/authService';

export function ProfileForm() {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? '');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [saving, setSaving] = useState(false);

  const onSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setSuccess(false);
    if (!fullName.trim()) {
      setError('Full name is required');
      return;
    }
    setError(null);
    setSaving(true);
    try {
      await updateProfile({ full_name: fullName.trim() });
      await refreshUser();
      setSuccess(true);
    } catch (err) {
      setError(getErrorMessage(err, 'Could not update your profile.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={(e) => void onSubmit(e)} noValidate>
      <Stack gap={4}>
        <AnimatedInput label="Email" value={user?.email ?? ''} readOnly disabled />
        <AnimatedInput label="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} error={error ?? undefined} />
        {success ? <Text role="status" color="green.500" fontSize="sm">Profile updated.</Text> : null}
        <GradientButton type="submit" disabled={saving} opacity={saving ? 0.7 : 1}>
          {saving ? 'Saving...' : 'Save changes'}
        </GradientButton>
      </Stack>
    </form>
  );
}
