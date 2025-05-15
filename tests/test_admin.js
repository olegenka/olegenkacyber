describe('Admin Panel Functions', () => {
    beforeEach(() => {
        // Мокаем DOM элементы
        document.body.innerHTML = `
            <div id="id_select"></div>
            <div id="status"></div>
            <div id="dop"></div>
            <div id="sats"></div>
            <div id="delay"></div>
            <div id="waiters"></div>
            <div id="mission_checkbox"></div>
            <div id="fly_accept_checkbox"></div>
            <input type="checkbox" id="monitoring-checkbox">
            <div id="main-buttons"></div>
            <div id="revised-mission-block"></div>
        `;
    });

    test('transformToAssocArray', () => {
        const result = transformToAssocArray('param1=value1&param2=value2');
        expect(result).toEqual({
            param1: 'value1',
            param2: 'value2'
        });
    });

    test('getSearchParameters', () => {
        // Мокаем window.location
        delete window.location;
        window.location = { search: '?token=test123' };
        
        const params = getSearchParameters();
        expect(params).toEqual({
            token: 'test123'
        });
    });

    test('copy_current_id', async () => {
        const mockClipboard = {
            writeText: jest.fn()
        };
        global.navigator.clipboard = mockClipboard;
        
        let active_id = 'test123';
        await copy_current_id();
        expect(mockClipboard.writeText).toHaveBeenCalledWith('test123');
    });

    test('customTileLoadFunction', () => {
        const imageTile = {
            getImage: () => ({ src: '' })
        };
        const src = 'https://mt1.google.com/vt/lyrs=y&x=1&y=2&z=3';
        
        let availableTiles = ['3/1/2'];
        customTileLoadFunction(imageTile, src);
        expect(imageTile.getImage().src).toBe('static/resources/tiles/3/1/2.png');
    });
});
