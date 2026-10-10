import { chakra } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { GOOGLE_LOGIN_URL } from '../../services/authService';

const MotionButton = motion.create(chakra.button);

export function GoogleLoginButton({ label = 'Continue with Google' }: { label?: string }) {
  return (
    <MotionButton
      type="button"
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      w="full"
      py={3}
      rounded="full"
      borderWidth="1px"
      borderColor="gray.300"
      bg="white"
      color="gray.800"
      fontWeight="semibold"
      cursor="pointer"
      onClick={() => window.location.assign(GOOGLE_LOGIN_URL)}
    >
      {label}
    </MotionButton>
  );
}
