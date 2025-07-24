import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import Events from '../../../frontend/src/pages/Events';

describe('Events Page', () => {
  it('renders static content', () => {
    const { container } = render(<Events />);
    expect(container).toMatchSnapshot();
  });
}); 