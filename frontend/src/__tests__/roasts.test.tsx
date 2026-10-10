import { screen } from '@testing-library/react';
import { RoastCard } from '../components/roasts/RoastCard';
import { ScoreBadge } from '../components/roasts/ScoreBadge';
import { TipList } from '../components/roasts/TipList';
import { makeTip, renderWithProviders } from '../test/utils';

describe('RoastCard', () => {
  it('renders roast text literally as plain text, never as HTML', () => {
    const evil = '<script>window.__pwned = true</script><img src=x onerror="window.__pwned=true"><b>bold</b>';
    const { container } = renderWithProviders(<RoastCard roastText={evil} />);
    expect(screen.getByText(evil)).toBeInTheDocument();
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('img')).toBeNull();
    expect(container.querySelector('b')).toBeNull();
    expect((window as unknown as { __pwned?: boolean }).__pwned).toBeUndefined();
  });

  it('preserves multi-line text', () => {
    renderWithProviders(<RoastCard roastText={'line one\nline two'} />);
    expect(screen.getByText(/line one/)).toHaveTextContent('line two');
  });
});

describe('ScoreBadge', () => {
  it.each([
    [100, 'green'],
    [75, 'green'],
    [74, 'yellow'],
    [50, 'yellow'],
    [49, 'orange'],
    [30, 'orange'],
    [29, 'red'],
    [0, 'red'],
  ])('score %i uses a %s color', (score, color) => {
    renderWithProviders(<ScoreBadge score={score} />);
    const badge = screen.getByLabelText(`Score ${score} out of 100`);
    expect(badge).toBeInTheDocument();
    expect(screen.getByText(String(score))).toBeInTheDocument();
    expect(getComputedStyle(badge).borderColor).toContain(`${color}-400`);
  });

  it('shows the denominator only for the large size', () => {
    const { unmount } = renderWithProviders(<ScoreBadge score={80} />);
    expect(screen.getByText('/ 100')).toBeInTheDocument();
    unmount();
    renderWithProviders(<ScoreBadge score={80} size="sm" />);
    expect(screen.queryByText('/ 100')).not.toBeInTheDocument();
  });
});

describe('TipList', () => {
  it('shows an empty-state message', () => {
    renderWithProviders(<TipList tips={[]} />);
    expect(screen.getByText(/Suspiciously clean/)).toBeInTheDocument();
  });

  it('groups tips by category in priority order', () => {
    renderWithProviders(
      <TipList
        tips={[
          makeTip({ id: 1, category: 'naming', title: 'N1' }),
          makeTip({ id: 2, category: 'bugs', title: 'B1' }),
          makeTip({ id: 3, category: 'naming', title: 'N2' }),
          makeTip({ id: 4, category: 'security', title: 'S1', file_path: 'app/auth.py' }),
        ]}
      />,
    );
    const labels = ['Bugs', 'Security', 'Naming'].map((l) => screen.getByText(l));
    // Document order: Bugs before Security before Naming
    expect(labels[0].compareDocumentPosition(labels[1]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(labels[1].compareDocumentPosition(labels[2]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.queryByText('Structure')).not.toBeInTheDocument();
    expect(screen.getByText('N1')).toBeInTheDocument();
    expect(screen.getByText('N2')).toBeInTheDocument();
    expect(screen.getByText('app/auth.py')).toBeInTheDocument();
  });

  it('renders tip descriptions as plain text', () => {
    const { container } = renderWithProviders(
      <TipList tips={[makeTip({ description: '<script>x()</script>' })]} />,
    );
    expect(screen.getByText('<script>x()</script>')).toBeInTheDocument();
    expect(container.querySelector('script')).toBeNull();
  });
});
