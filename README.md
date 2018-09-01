# Crawl_Ptt

1.使用requests、requests_html等library  
2.抓取Ptt網頁版資料，自html5抓每篇文章連結、標題、作者及更早的文章連結等資訊  
3.把抓到的文章連結、標題等資訊放到database紀錄已爬過的文章，這裡使用sqlite  
4.爬文章內容及圖片連結、將圖片抓入本機硬碟  
