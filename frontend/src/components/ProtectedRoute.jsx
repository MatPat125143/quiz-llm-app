import { Navigate, useLocation } from 'react-router-dom';

function decodeJwtPayload(token) {
    try {
        const payloadPart = token.split('.')[1];
        if (!payloadPart) return null;

        const base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/');
        const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');

        return JSON.parse(atob(padded));
    } catch {
        return null;
    }
}

function isAccessTokenValid(token) {
    const payload = decodeJwtPayload(token);
    if (!payload || typeof payload.exp !== 'number') return false;

    const nowInSeconds = Math.floor(Date.now() / 1000);
    return payload.exp > nowInSeconds;
}

export default function ProtectedRoute({ children }) {
    const location = useLocation();
    const token = localStorage.getItem('access_token');

    if (!token || !isAccessTokenValid(token)) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return children;
}
