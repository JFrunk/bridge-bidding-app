import React from 'react';
import PropTypes from 'prop-types';
import './Buttons.css';

/**
 * Button - Three button tiers used across all learning flows
 *
 * @param {Object} props
 * @param {'primary' | 'secondary' | 'on-felt'} props.variant - Button style
 * @param {React.ReactNode} props.children - Button content
 * @param {function} props.onClick - Click handler
 * @param {boolean} props.disabled - Disabled state
 * @param {React.ReactNode} props.icon - Optional icon before text
 */
const Button = ({
  variant = 'primary',
  children,
  onClick,
  disabled = false,
  icon,
  ...rest
}) => {
  const className = `btn btn-${variant}`;

  return (
    <button
      className={className}
      onClick={onClick}
      disabled={disabled}
      {...rest}
    >
      {icon && <span className="btn-icon">{icon}</span>}
      {children}
    </button>
  );
};

Button.propTypes = {
  variant: PropTypes.oneOf(['primary', 'secondary', 'on-felt']),
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  disabled: PropTypes.bool,
  icon: PropTypes.node,
};

/**
 * PrimaryButton - Gold/accent button for primary actions
 */
const PrimaryButton = (props) => <Button variant="primary" {...props} />;

/**
 * SecondaryButton - Subtle button for secondary actions
 */
const SecondaryButton = (props) => <Button variant="secondary" {...props} />;

/**
 * OnFeltButton - Glass-style button for use on felt/green backgrounds
 */
const OnFeltButton = (props) => <Button variant="on-felt" {...props} />;

export { Button, PrimaryButton, SecondaryButton, OnFeltButton };
export default Button;
