// Проверка наличия необходимых модулей
try {
    var axios = require('axios');
} catch (error) {
    console.error('❌ Модуль axios не установлен. Установите его командой:');
    console.error('npm install axios');
    process.exit(1);
}

const fs = require('fs');
const path = require('path');

async function sendQuantumCircuit() {
    try {
        const graphsDir = path.join(__dirname, 'graphs');
        const resultsBaseDir = path.join(__dirname, 'quantum_results');
        
        // Проверка существования папки graphs
        if (!fs.existsSync(graphsDir)) {
            throw new Error(`Папка graphs не найдена: ${graphsDir}`);
        }

        // Создание основной папки для результатов
        if (!fs.existsSync(resultsBaseDir)) {
            fs.mkdirSync(resultsBaseDir);
            console.log(`✅ Создана папка для результатов: ${resultsBaseDir}`);
        }

        // Чтение всех подпапок в graphs
        const graphFolders = fs.readdirSync(graphsDir)
            .filter(item => {
                const itemPath = path.join(graphsDir, item);
                return fs.statSync(itemPath).isDirectory() && item.startsWith('graph_');
            })
            .sort((a, b) => {
                // Сортировка по номеру графа
                const numA = parseInt(a.replace('graph_', ''));
                const numB = parseInt(b.replace('graph_', ''));
                return numA - numB;
            });

        if (graphFolders.length === 0) {
            throw new Error('В папке graphs не найдено папок graph_N');
        }

        console.log(`Найдено графов: ${graphFolders.length}`);

        const results = [];

        // Обработка каждого графа
        for (const graphFolder of graphFolders) {
            const graphPath = path.join(graphsDir, graphFolder);
            console.log(`\n📊 Обработка графа: ${graphFolder}`);
            
            // Создание папки для результатов этого графа
            const graphResultsDir = path.join(resultsBaseDir, graphFolder);
            if (!fs.existsSync(graphResultsDir)) {
                fs.mkdirSync(graphResultsDir, { recursive: true });
            }

            // Чтение всех JSON файлов в папке графа
            const jsonFiles = fs.readdirSync(graphPath)
                .filter(file => file.endsWith('.json') && file.includes('api_payload_car_'))
                .sort();

            if (jsonFiles.length === 0) {
                console.log(`❌ В папке ${graphFolder} не найдено JSON файлов с api_payload_car_`);
                continue;
            }

            console.log(`📁 Найдено файлов: ${jsonFiles.length}`);

            // Обработка каждого JSON файла
            for (const jsonFile of jsonFiles) {
                const configPath = path.join(graphPath, jsonFile);
                console.log(`   🔄 Обработка файла: ${jsonFile}`);

                try {
                    const circuitData = JSON.parse(fs.readFileSync(configPath, 'utf8'));

                    // Настройки API
                    const apiUrl = 'https://mireatom.mirea.ru/kraniki/circuit/api';
                    const auth = {
                        username: 'mirxbo@yandex.ru',
                        password: '68ae1805cab0d63b268dbdd40cf41aad'
                    };

                    console.log(`      📤 Отправка данных на сервер...`);
                    const response = await axios.post(apiUrl, circuitData, {
                        auth,
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        timeout: 10000
                    });

                    // Извлечение номера машины из имени файла
                    const carNumberMatch = jsonFile.match(/api_payload_car_(\d+)/);
                    const carNumber = carNumberMatch ? carNumberMatch[1] : 'unknown';

                    // Создание имени файла результата
                    const outputFilename = `Result_${graphFolder}_car_${carNumber}.json`;
                    const outputPath = path.join(graphResultsDir, outputFilename);

                    // Обработка ответа
                    let resultData;
                    if (response.data.data && Array.isArray(response.data.data)) {
                        resultData = response.data;
                    } else if (response.data.status === true && response.data.data && typeof response.data.data === 'object') {
                        resultData = {
                            data: Object.entries(response.data.data).map(([bitstring, value]) => ({
                                bitstring,
                                value
                            }))
                        };
                    } else {
                        throw new Error('Неизвестный формат ответа от сервера');
                    }

                    // Сохранение файла
                    fs.writeFileSync(outputPath, JSON.stringify(resultData, null, 2));
                    console.log(`      ✅ Результат сохранен: ${outputFilename}`);

                    results.push({
                        success: true,
                        graph: graphFolder,
                        file: jsonFile,
                        carNumber: carNumber,
                        outputPath: outputPath,
                        data: resultData
                    });

                    // Небольшая задержка между запросами чтобы не перегружать сервер
                    await new Promise(resolve => setTimeout(resolve, 1000));

                } catch (fileError) {
                    console.error(`      ❌ Ошибка при обработке файла ${jsonFile}:`, fileError.message);
                    
                    if (fileError.response) {
                        console.error('      Статус:', fileError.response.status);
                        if (fileError.response.data) {
                            console.error('      Данные ошибки:', JSON.stringify(fileError.response.data, null, 2));
                        }
                    }

                    results.push({
                        success: false,
                        graph: graphFolder,
                        file: jsonFile,
                        error: fileError.message
                    });
                }
            }
        }

        // Создание общего файла с результатами
        const summary = {
            timestamp: new Date().toISOString(),
            totalProcessed: results.length,
            successful: results.filter(r => r.success).length,
            failed: results.filter(r => !r.success).length,
            results: results.map(r => ({
                graph: r.graph,
                file: r.file,
                carNumber: r.carNumber,
                success: r.success,
                outputPath: r.outputPath || null,
                error: r.error || null
            }))
        };

        const summaryPath = path.join(resultsBaseDir, 'processing_summary.json');
        fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
        console.log(`\n📊 Общий отчет сохранен: ${summaryPath}`);

        // Сводка результатов
        console.log('\n=== СВОДКА РЕЗУЛЬТАТОВ ===');
        console.log(`📁 Общая папка с результатами: ${resultsBaseDir}`);
        console.log(`✅ Успешно обработано: ${summary.successful}`);
        console.log(`❌ Ошибок: ${summary.failed}`);
        console.log(`📊 Всего файлов: ${summary.totalProcessed}`);
        
        if (summary.failed > 0) {
            console.log('\n📋 Ошибочные файлы:');
            results.filter(r => !r.success).forEach(r => {
                console.log(`   - ${r.graph}/${r.file}: ${r.error}`);
            });
        }

        console.log(`\n🎯 Структура результатов:`);
        console.log(`   ${resultsBaseDir}/`);
        graphFolders.forEach(folder => {
            const resultFiles = results.filter(r => r.graph === folder && r.success);
            console.log(`   ├── ${folder}/ (${resultFiles.length} файлов)`);
        });
        console.log(`   └── processing_summary.json`);

        return summary;

    } catch (error) {
        console.error('❌ Критическая ошибка:', error.message);

        if (error.response) {
            console.error('Статус:', error.response.status);
            console.error('Данные:', error.response.data);
        }

        return {
            success: false,
            error: error.message
        };
    }
}

function pad(num) {
    return num.toString().padStart(2, '0');
}

module.exports = { sendQuantumCircuit };

if (require.main === module) {
    sendQuantumCircuit();
}
