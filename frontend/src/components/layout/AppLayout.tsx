import { useEffect } from 'react';
import { Box, Button, Flex, HStack } from '@chakra-ui/react';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { applyMode, readStoredMode } from '../../hooks/useColorMode';

interface NavItem {
  to: string;
  label: string;
}

const LINKS: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/submissions/new', label: 'Submit' },
  { to: '/submissions', label: 'Submissions' },
  { to: '/roasts', label: 'Roasts' },
  { to: '/profile', label: 'Profile' },
];

export function AppLayout() {
  const { logout } = useAuth();

  useEffect(() => {
    applyMode(readStoredMode());
  }, []);

  return (
    <Box>
      <Flex as="nav" align="center" justify="space-between" wrap="wrap" gap={2} px={6} py={3} borderBottomWidth="1px" bg="bg.panel">
        <HStack gap={4} wrap="wrap">
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.to === '/submissions'}>
              {({ isActive }) => <Box fontWeight={isActive ? 'bold' : 'normal'}>{l.label}</Box>}
            </NavLink>
          ))}
        </HStack>
        <Button size="sm" variant="outline" onClick={() => void logout()}>
          Logout
        </Button>
      </Flex>
      <Outlet />
    </Box>
  );
}
