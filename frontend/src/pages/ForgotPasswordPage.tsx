import { useState, type FormEvent } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Center, Heading, Stack, Text } from '@chakra-ui/react';
import { MeshBackground } from '../components/layout/MeshBackground';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { AnimatedInput } from '../components/ui/AnimatedInput';
import { GradientButton } from '../components/ui/GradientButton';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const onSubmit = (e: FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <PageWrapper>
      <MeshBackground />
      <Center minH="80vh">
        <GlassCard w="full" maxW="md">
          <Heading size="2xl" mb={1}>Forgot password?</Heading>
          <Text color="fg.muted" mb={6}>Enter your email and we will help you get back in.</Text>
          <form onSubmit={onSubmit}>
            <Stack gap={4}>
              <AnimatedInput label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              <GradientButton type="submit">Send reset link</GradientButton>
              {submitted ? (
                <Text role="status" color={{ base: 'purple.600', _dark: 'purple.300' }} fontSize="sm">
                  Password reset is coming soon. For now, please contact your trainer to have your password reset.
                </Text>
              ) : null}
              <RouterLink to="/login">
                <Text as="span" color={{ base: 'purple.600', _dark: 'purple.300' }} fontSize="sm">Back to sign in</Text>
              </RouterLink>
            </Stack>
          </form>
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
