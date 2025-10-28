import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button } from '../button'; // Adjust the import path if necessary

describe('Button Component', () => {
  it('renders the button with the correct text', () => {
    render(<Button>Click Me</Button>);

    // Check if the button is in the document
    const buttonElement = screen.getByRole('button', { name: /click me/i });
    expect(buttonElement).toBeInTheDocument();

    // Check for the text content
    expect(buttonElement).toHaveTextContent('Click Me');
  });

  it('applies the correct default variant', () => {
    render(<Button>Default Button</Button>);
    const buttonElement = screen.getByRole('button', { name: /default button/i });

    // Shadcn buttons often have a default class for the variant
    // This is an example, the actual class might differ.
    expect(buttonElement).toHaveClass('bg-primary');
  });
});
