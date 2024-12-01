INSERT INTO `User` (username, email, password, bio) VALUES
('Abdulkadir', 'abdulkadirkk42@gmail.com', 'password123', 'Doğa sever ve teknoloji meraklısı'),
('Ahmet', 'ahmett52@gmail.com', 'password456', 'Spor ve müzikle ilgileniyor'),
('Emre', 'emre34@gmail.com', 'password789', 'Yazılım geliştirme konusunda tutkulu'),
('Serpil', 'serpil@gmail.com', 'password101', 'Kitap okumayı seven bir insan'),
('Arda', 'ardagüler@gmail.com', 'password112', 'Sinema tutkunu ve gezgin'),
('Ayşe', 'ayse@gmail.com', 'password131', 'Ailevi işlerle meşgul ve gönüllü çalışmalara katılır'),
('Zeynep', 'zeynep@gmail.com', 'password415', 'Sosyal medya ve dijital pazarlama uzmanı');




INSERT INTO `Group` (group_name, group_description, created_by) VALUES
('Trekking', 'Her hafta sonu doğa yürüyüşleri düzenleriz.', 1),
('Okçuluk Kulübü', 'Okçuluk ve her şey', 3),
('Müzik ve Konserler', 'Canlı müzik geceleri, konserler ve dahası', 7);


INSERT INTO `Membership` (user_id, group_id, user_role) VALUES
(1, 1, 'Admin'),
(2, 1, 'Member'),
(3, 2, 'Member'),
(4, 3, 'Admin'),
(5, 2, 'Guest'),
(6, 3, 'Member'),
(7, 1, 'Admin');



INSERT INTO `Event` (group_id, event_name, event_description, event_date, event_location) VALUES
(1, 'Doğa Yürüyüşü - Aralık', 'Kışın en güzel doğa yürüyüşü', '2024-12-10', 'Çamlıca Tepesi'),
(2, 'Okçuluk Turnuvası', 'Eğlenceli bir okçuluk turnuvası', '2024-12-15', 'Atatürk Ormanı'),
(3, 'Yeni Yıl Konseri', 'Yılbaşı öncesi bir konser etkinliği', '2024-12-25', 'Beyoğlu Konser Salonu');



INSERT INTO `Event_Attendance` (user_id, event_id, event_status) VALUES
(1, 1, 'Attended'),
(2, 1, 'Interested'),
(3, 2, 'Not Attended'),
(4, 3, 'Attended'),
(5, 2, 'Attended'),
(6, 3, 'Interested'),
(7, 1, 'Not Attended');



INSERT INTO `Feedback` (user_id, event_id, rating, feedback) VALUES
(1, 1, 5, 'Harika bir etkinlikti, çok keyif aldım!'),
(2, 1, 4, 'Güzel bir yürüyüş, ancak biraz daha fazla rehber olabilir.'),
(3, 2, 3, 'Katılamadım ama etkinlik fikri hoştu.'),
(4, 3, 5, 'Konser mükemmeldi, harika bir atmosfer vardı.'),
(5, 2, 4, 'Okçuluk turnuvası çok eğlenceliydi, daha fazla katılım beklerdim.'),
(6, 3, 5, 'Yeni yıl konseri harikaydı, müzik çok iyiydi.'),
(7, 1, 2, 'Yürüyüş güzeldi ama hava soğuktu.');



INSERT INTO `Message_Board` (group_id, user_id, user_message) VALUES
(1, 1, 'Doğa yürüyüşü için hazırlıklara başladık, katılacak olan var mı?'),
(2, 3, 'Okçuluk turnuvası için kayıtlar başladı, herkesi bekliyoruz!'),
(3, 4, 'Yeni yıl konserine bilet almayı unutmayın, yerler sınırlı!');



INSERT INTO `Tag` (tag_name) VALUES
('Doğa'),
('Spor'),
('Müzik'),
('Yeni Yıl');



INSERT INTO `Event_Tag` (event_id, tag_id) VALUES
(1, 1),
(2, 2),
(3, 3),
(3, 4);
