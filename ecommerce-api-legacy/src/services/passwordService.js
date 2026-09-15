const bcrypt = require('bcryptjs');
const settings = require('../config/settings');

function hash(plainPassword) {
    return bcrypt.hash(plainPassword, settings.bcryptSaltRounds);
}

function compare(plainPassword, passwordHash) {
    return bcrypt.compare(plainPassword, passwordHash);
}

module.exports = { hash, compare };
