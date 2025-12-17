import { BrowserRouter } from 'react-router-dom';
import AppRouter from './routes/AppRouter';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
    return (
        <BrowserRouter>
            <ErrorBoundary>
                <AppRouter />
            </ErrorBoundary>
        </BrowserRouter>
    );
}

export default App;
