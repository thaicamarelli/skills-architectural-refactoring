require('dotenv').config();

function required(name) {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Variável de ambiente obrigatória ausente: ${name}`);
    }
    return value;
}

const settings = {
    port: Number(process.env.PORT) || 3000,
    dbUser: required('DB_USER'),
    dbPass: required('DB_PASS'),
    paymentGatewayKey: required('PAYMENT_GATEWAY_KEY'),
    smtpUser: process.env.SMTP_USER || 'no-reply@fullcycle.com.br',
    adminApiKey: required('ADMIN_API_KEY'),
    bcryptSaltRounds: Number(process.env.BCRYPT_SALT_ROUNDS) || 12,
};

module.exports = settings;
