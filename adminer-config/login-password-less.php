<?php

/** Adminer plugin to allow access to SQLite databases without passwords
 * Based on Adminer documentation: https://www.adminer.org/en/password/
 * This plugin sets up a dummy password for Adminer but doesn't pass it to SQLite
 * @author Jakub Vrana, https://www.vrana.cz/
 * @license https://www.apache.org/licenses/LICENSE-2.0 Apache License, Version 2.0
 * @license https://www.gnu.org/licenses/gpl-2.0.html GNU General Public License, version 2 (one or other)
 */
class AdminerLoginPasswordLess {
	private $password;

	function __construct($password = "") {
		$this->password = $password;
	}

	function login($login, $password) {
		return ($password == $this->password);
	}

	function loginForm() {
		echo "<table cellspacing='0'>\n";
		echo "<tr><th>" . lang('Username') . "<td><input name='auth[driver]' value='server' type='hidden'><input name='auth[server]' value='" . h(SERVER) . "' title='" . lang('Server') . "' autocapitalize='off'>\n";
		echo "<tr><th>" . lang('Password') . "<td><input type='password' name='auth[password]' placeholder='admin' autocomplete='current-password'>\n";
		echo "</table>\n";
		echo "<p><input type='submit' value='" . lang('Login') . "'>\n";
		echo checkbox("auth[permanent]", 1, $_COOKIE["adminer_permanent"], lang('Permanent login')) . "\n";
		echo "<p class='message'>" . lang('Use password: admin') . "\n";
	}

	function database() {
		// For SQLite, return the database file path
		if (preg_match('~^sqlite:(.*)~', SERVER, $match)) {
			return $match[1];
		}
		return DB;
	}

	function connect() {
		// For SQLite databases, connect without authentication
		if (preg_match('~^sqlite:(.*)~', SERVER, $match)) {
			$connection = new Min_SQLite($match[1]);
			return $connection;
		}
		return false;
	}
}

// Initialize plugin with default password "admin"
return new AdminerLoginPasswordLess("admin");
