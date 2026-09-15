const logger = require('./loggerService');

const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

// Simulação do gateway real: cartões que começam com "4" (bandeira Visa de teste) são aprovados.
const APPROVED_CARD_PREFIX = '4';

function charge(cardNumber) {
    const last4 = cardNumber.slice(-4);
    logger.info('payment.processing', { cardLast4: last4 });

    const status = cardNumber.startsWith(APPROVED_CARD_PREFIX)
        ? PAYMENT_STATUS.PAID
        : PAYMENT_STATUS.DENIED;

    return { status };
}

module.exports = { charge, PAYMENT_STATUS };
