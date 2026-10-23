import { AppConfigProvider } from "../appcontext/appConfig";
import Header from "../components/header";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {

  return (
    <AppConfigProvider>
      <Header 
        heading={'Competitor Report'} 
        subheading={'Your current summary and consolidated report for competitors.'} 
        headerButtons={false} 
        calculationformula={'请注意：金额是到千位的不含税金额，如果竞品的销售是100万，请填写1000！如果去年同期数据有误，请发邮件告知且说明原因！'} />
        {children}
      {/* <Footer /> */}
    </AppConfigProvider>
  );
}
