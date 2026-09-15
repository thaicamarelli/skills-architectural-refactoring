const { HttpError } = require('../middlewares/errorHandler');
const passwordService = require('../services/passwordService');
const paymentService = require('../services/paymentService');

function validateCheckoutInput({ username, email, courseId, cardNumber }) {
    if (!username || !email || !courseId || !cardNumber) {
        throw new HttpError(400, 'Bad Request');
    }
}

function makeCheckoutController({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel }) {
    return async function checkout(req, res) {
        const { usr: username, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

        validateCheckoutInput({ username, email, courseId, cardNumber });

        const course = await courseModel.findActiveById(courseId);
        if (!course) throw new HttpError(404, 'Curso não encontrado');

        let user = await userModel.findByEmail(email);
        if (!user) {
            const passwordHash = await passwordService.hash(password || '123456');
            const userId = await userModel.create({ name: username, email, passwordHash });
            user = { id: userId };
        }

        const { status } = paymentService.charge(cardNumber);
        if (status === paymentService.PAYMENT_STATUS.DENIED) {
            throw new HttpError(400, 'Pagamento recusado');
        }

        const enrollmentId = await db.transaction(async () => {
            const id = await enrollmentModel.create(user.id, courseId);
            await paymentModel.create(id, course.price, status);
            await auditLogModel.create(`Checkout curso ${courseId} por ${user.id}`);
            return id;
        });

        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    };
}

module.exports = makeCheckoutController;
