import { useCallback, useEffect, useState } from 'react';
import { getCurrentUser } from '../services/api';

export default function useCurrentUser(options = {}) {
  const { autoLoad = true } = options;
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(autoLoad);
  const [error, setError] = useState(null);

  const refreshUser = useCallback(async () => {
    try {
      setError(null);
      const data = await getCurrentUser();
      setUser(data);
      return data;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!autoLoad) {
      setLoading(false);
      return;
    }

    let isMounted = true;
    (async () => {
      try {
        setError(null);
        const data = await getCurrentUser();
        if (isMounted) setUser(data);
      } catch (err) {
        if (isMounted) setError(err);
      } finally {
        if (isMounted) setLoading(false);
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [autoLoad]);

  return {
    user,
    setUser,
    loading,
    error,
    refreshUser,
  };
}
