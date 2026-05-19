import { useAppSettings } from '../hooks/useAppSettings';
import zhCN from './zh-CN';
import enUS from './en-US';

type Translations = typeof zhCN;

const translations: Record<string, Translations> = {
  'zh-CN': zhCN,
  'en-US': enUS,
};

export function useTranslation() {
  const { locale } = useAppSettings();
  const t = translations[locale] || zhCN;

  return { t, locale, isZh: locale === 'zh-CN' };
}
