import React from 'react';
import './App.css';
import Layout from './components/Layout';
import Header from './components/Header';
import Footer from './components/Footer';
import MainContent from './components/MainContent';

function App() {
  return (
    <Layout
      header={<Header />}
      footer={<Footer />}
    >
      <MainContent />
    </Layout>
  );
}

export default App;
