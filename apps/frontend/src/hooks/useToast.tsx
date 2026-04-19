import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';

interface Toast {
    id: number;
    type: 'success' | 'error' | 'info';
    text: string;
}

interface ToastContextType {
    toasts: Toast[];
    addToast: (type: Toast['type'], text: string) => void;
    removeToast: (id: number) => void;
}

const ToastContext = createContext<ToastContextType>({
    toasts: [],
    addToast: () => { },
    removeToast: () => { },
});

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const removeToast = useCallback((id: number) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const addToast = useCallback((type: Toast['type'], text: string) => {
        const id = nextId++;
        setToasts((prev) => [...prev, { id, type, text }]);
        // Auto-dismiss after 4s
        setTimeout(() => removeToast(id), 4000);
    }, [removeToast]);

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
            {children}
        </ToastContext.Provider>
    );
}

export function useToast() {
    return useContext(ToastContext);
}

export function ToastContainer() {
    const { toasts, removeToast } = useToast();

    if (toasts.length === 0) return null;

    return (
        <div className="max-w-5xl mx-auto px-6 pt-4">
            {toasts.map((toast) => (
                <div
                    key={toast.id}
                    className={`flash flash-${toast.type} mb-2 cursor-pointer`}
                    onClick={() => removeToast(toast.id)}
                >
                    {toast.text}
                </div>
            ))}
        </div>
    );
}
