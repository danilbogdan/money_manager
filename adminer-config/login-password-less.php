<?php
require_once('plugins/login-password-less.php');

/** Set allowed password for Adminer login
 * Password: admin
 * This allows access to SQLite without database authentication
 */
return new AdminerLoginPasswordLess(
    $password_hash = password_hash('admin', PASSWORD_DEFAULT)
);
