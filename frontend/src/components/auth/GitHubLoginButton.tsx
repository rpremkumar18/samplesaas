import { chakra } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { GITHUB_LOGIN_URL } from '../../services/authService';

const MotionButton = motion.create(chakra.button);

export function GitHubLoginButton({ label = 'Continue with GitHub' }: { label?: string }) {
  return (
    <MotionButton
      type="button"
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      w="full"
      py={3}
      rounded="full"
      borderWidth="1px"
      borderColor="border.emphasized"
      bg={{ base: 'white', _dark: 'whiteAlpha.100' }}
      color="fg"
      fontWeight="semibold"
      cursor="pointer"
      onClick={() => window.location.assign(GITHUB_LOGIN_URL)}
    >
      {label}
    </MotionButton>
  );
}
