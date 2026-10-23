import { AppConfigProvider } from "../appcontext/appConfig";
import { FileUtilityProvider } from "../appcontext/fileUtilityContext";
import Header from "../components/header";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AppConfigProvider>
        <FileUtilityProvider>
          <Header 
            heading={'Competitor Report'} 
            subheading={'Your current summary and consolidated report for competitors.'} 
            headerButtons={true} />
            {children}
          {/* <Footer /> */}
        </FileUtilityProvider>
    </AppConfigProvider>
  );
}
