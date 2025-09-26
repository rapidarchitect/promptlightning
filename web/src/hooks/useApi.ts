import { useState, useEffect, useCallback } from 'react';
import { api, ApiError } from '../utils/api';
import type { Template } from '../types';

export function useTemplates() {
  const [templates, setTemplates] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTemplates = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getTemplates();
      setTemplates(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch templates');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  return { templates, loading, error, refetch: fetchTemplates };
}

export function useTemplate(id: string | null) {
  const [template, setTemplate] = useState<Template | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTemplate = useCallback(async (templateId: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getTemplate(templateId);
      setTemplate(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch template');
      setTemplate(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (id) {
      fetchTemplate(id);
    } else {
      setTemplate(null);
      setError(null);
    }
  }, [id, fetchTemplate]);

  return { template, loading, error, refetch: id ? () => fetchTemplate(id) : undefined };
}

export function useExamples() {
  const [examples, setExamples] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchExamples() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getExamples();
        setExamples(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch examples');
      } finally {
        setLoading(false);
      }
    }

    fetchExamples();
  }, []);

  return { examples, loading, error };
}

export function useRender() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const render = useCallback(async (templateId: string, inputs: Record<string, unknown>) => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.renderTemplate(templateId, { inputs });
      return response;
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : err instanceof Error
        ? err.message
        : 'Failed to render template';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { render, loading, error, clearError: () => setError(null) };
}

export function useCreateTemplate() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createTemplate = useCallback(async (template: Omit<Template, 'inputs'> & {
    inputs: Record<string, { type: string; required: boolean; default?: unknown }>
  }) => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.createTemplate(template);
      return response;
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : err instanceof Error
        ? err.message
        : 'Failed to create template';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { createTemplate, loading, error, clearError: () => setError(null) };
}

export function useUpdateTemplate() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateTemplate = useCallback(async (id: string, template: Partial<Omit<Template, 'id' | 'inputs'>> & {
    inputs?: Record<string, { type: string; required: boolean; default?: unknown }>
  }) => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.updateTemplate(id, template);
      return response;
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : err instanceof Error
        ? err.message
        : 'Failed to update template';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { updateTemplate, loading, error, clearError: () => setError(null) };
}